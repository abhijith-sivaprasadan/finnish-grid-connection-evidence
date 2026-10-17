"""Resolve the existing Neon project's PostgreSQL URI with safe, staged errors.

This runs only inside an authorized GitHub Actions workflow. The API token,
password, full URL and raw Neon responses are NEVER written to logs.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re

import requests

API = "https://console.neon.tech/api/v2"
SAFE_ID = re.compile(r"^[a-z0-9-]{1,60}$")
SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]{1,100}$")


class NeonLookupError(ValueError):
    """Categorized error that contains no credentials or raw provider output."""


def _get(session, path, api_key, *, stage, params=None):
    try:
        response = session.get(
            API + path,
            headers={"Authorization": "Bearer " + api_key,
                     "Accept": "application/json"},
            params=params, timeout=(10, 30), allow_redirects=False)
    except requests.RequestException:
        raise NeonLookupError(f"{stage}: NETWORK_OR_TIMEOUT") from None
    if response.status_code != 200:
        # Never report the response body, token or the full request URL.
        raise NeonLookupError(f"{stage}: HTTP_{response.status_code}") from None
    try:
        payload = response.json()
    except (ValueError, TypeError):
        raise NeonLookupError(f"{stage}: INVALID_JSON") from None
    if not isinstance(payload, dict):
        raise NeonLookupError(f"{stage}: UNEXPECTED_JSON_SHAPE")
    return payload


def _available_names(items):
    """Print only validated branch labels, never raw third-party API values."""
    names = sorted({item.get("name") for item in items
                    if isinstance(item, dict)
                    and isinstance(item.get("name"), str)
                    and SAFE_NAME.fullmatch(item["name"])})
    return ", ".join(names[:15]) or "(none identifiable)"


def resolve_connection(project_id, api_key, *, branch_name="main",
                       database_name=None, session=None):
    """Retrieve an existing branch + DB owner and direct TLS connection URI.

    A missing requested branch is NEVER silently replaced by the default.
    """
    if not isinstance(project_id, str) or not SAFE_ID.fullmatch(project_id):
        raise NeonLookupError("CONFIG: invalid NEON_PROJECT_ID")
    if not isinstance(api_key, str) or not api_key.strip():
        raise NeonLookupError("CONFIG: missing NEON_API_KEY")
    if not isinstance(branch_name, str) or not SAFE_NAME.fullmatch(branch_name):
        raise NeonLookupError("CONFIG: invalid NEON_BRANCH_NAME")
    if database_name is not None and (not isinstance(database_name, str)
                                      or not SAFE_NAME.fullmatch(database_name)):
        raise NeonLookupError("CONFIG: invalid NEON_DATABASE_NAME")
    s = session or requests.Session()
    project_path = f"/projects/{project_id}"
    branches = _get(s, project_path + "/branches", api_key,
                    stage="LIST_BRANCHES").get("branches")
    if not isinstance(branches, list):
        raise NeonLookupError("LIST_BRANCHES: response missing branches array")
    matches = [item for item in branches
               if isinstance(item, dict) and item.get("name") == branch_name]
    if len(matches) != 1:
        raise NeonLookupError(
            f"BRANCH_NOT_FOUND: selected '{branch_name}' is not a unique branch; "
            f"available branch names: {_available_names(branches)}. "
            "Choose one of those values in the manual workflow's Neon branch field.")
    if not SAFE_ID.fullmatch(str(matches[0].get("id", ""))):
        raise NeonLookupError("LIST_BRANCHES: selected branch ID is malformed")
    branch_id = matches[0]["id"]

    databases = _get(
        s, project_path + f"/branches/{branch_id}/databases", api_key,
        stage="LIST_DATABASES").get("databases")
    if not isinstance(databases, list):
        raise NeonLookupError("LIST_DATABASES: response missing databases array")
    if database_name:
        choices = [x for x in databases if isinstance(x, dict)
                   and x.get("name") == database_name]
    else:
        choices = [x for x in databases if isinstance(x, dict)]
        if len(choices) > 1:
            choices = [x for x in choices if x.get("name") == "neondb"]
    if len(choices) != 1:
        raise NeonLookupError(
            "DATABASE_NOT_FOUND_OR_AMBIGUOUS: set NEON_DATABASE_NAME "
            "to an existing database in the selected branch")
    chosen = choices[0]
    name, role = chosen.get("name"), chosen.get("owner_name")
    if not isinstance(name, str) or not name or not isinstance(role, str) or not role:
        raise NeonLookupError(
            "LIST_DATABASES: selected database has no discoverable owner role")

    connection = _get(
        s, project_path + "/connection_uri", api_key,
        stage="GET_CONNECTION_URI",
        params={"branch_id": branch_id, "database_name": name,
                "role_name": role, "pooled": "false"}).get("uri")
    if not isinstance(connection, str) or not connection.startswith(
            ("postgres://", "postgresql://")) or any(
            char in connection for char in "\r\n"):
        raise NeonLookupError("GET_CONNECTION_URI: no valid PostgreSQL URI returned")
    try:
        from src.cloud_store import engine_for
        engine = engine_for(connection)
        engine.dispose()
    except Exception:
        # Driver validation failures may contain credential-bearing URLs.
        raise NeonLookupError("GET_CONNECTION_URI: returned URI failed TLS/driver validation") from None
    return {"uri": connection, "project_id": project_id,
            "branch": branch_name, "database_name": name, "role_name": role}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--export-github-env", action="store_true",
                   help="Mask credentials and hand the URI to subsequent Actions steps")
    args = p.parse_args(argv)
    try:
        result = resolve_connection(
            os.environ.get("NEON_PROJECT_ID", ""),
            os.environ.get("NEON_API_KEY", ""),
            branch_name=os.environ.get("NEON_BRANCH_NAME", "main"),
            database_name=os.environ.get("NEON_DATABASE_NAME") or None)
        if args.export_github_env:
            target = os.environ.get("GITHUB_ENV")
            if not target:
                raise NeonLookupError("CONFIG: GITHUB_ENV is absent")
            from sqlalchemy.engine import make_url
            raw = result["uri"]
            password = make_url(raw).password
            if password:
                print("::add-mask::" + password, flush=True)
            print("::add-mask::" + raw, flush=True)
            with Path(target).open("a", encoding="utf-8") as f:
                f.write("DATABASE_WRITE_URL=" + raw + "\n")
        print("Neon connection resolved for selected branch; credentials are masked.")
    except NeonLookupError as exc:
        p.exit(2, f"Neon connection discovery failed: {exc}\n")
    except Exception:
        # Do not print unexpected exceptions that may embed private URIs.
        p.exit(2, "Neon connection discovery failed: UNCLASSIFIED_LOCAL_ERROR; "
                   "no credentials printed.\n")


if __name__ == "__main__":
    main()
