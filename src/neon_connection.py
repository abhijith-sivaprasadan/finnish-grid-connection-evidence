"""Resolve the existing Neon project's Postgres URI using GitHub integration.

Runs only in an explicitly authorized GitHub Actions job. No URI, API token,
password, Neon response body or full HTTP request URL is ever printed.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys

import requests

API = "https://console.neon.tech/api/v2"
SAFE_ID = re.compile(r"^[a-z0-9-]{1,60}$")


def _get(session, path, api_key, params=None):
    try:
        response = session.get(
            API + path, headers={"Authorization": "Bearer " + api_key,
                                 "Accept": "application/json"},
            params=params, timeout=(10, 30), allow_redirects=False)
    except requests.RequestException as exc:
        raise RuntimeError("Neon API request failed (network or timeout)") from None
    if response.status_code != 200:
        # Never expose error text: some API responses contain sensitive fields.
        raise RuntimeError(f"Neon API returned HTTP {response.status_code}") from None
    try:
        payload = response.json()
    except (ValueError, TypeError):
        raise RuntimeError("Neon returned malformed API JSON") from None
    if not isinstance(payload, dict):
        raise RuntimeError("Neon returned an unexpected API response")
    return payload


def resolve_connection(project_id, api_key, *, branch_name="main",
                       database_name=None, session=None):
    """Discover actual branch/database owner, then get their direct SSL URL.

    No guessed role names or branch IDs are used. Multiple databases require an
    explicit name. Defaults to Neon's canonical 'main', not a hidden fallback.
    """
    if not isinstance(project_id, str) or not SAFE_ID.fullmatch(project_id):
        raise ValueError("Invalid NEON_PROJECT_ID")
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("Missing NEON_API_KEY")
    if not isinstance(branch_name, str) or not branch_name.strip():
        raise ValueError("Missing Neon branch name")
    s = session or requests.Session()
    project_path = f"/projects/{project_id}"
    branches = _get(s, project_path + "/branches", api_key).get("branches")
    if not isinstance(branches, list):
        raise ValueError("Neon response did not contain branches")
    matches = [item for item in branches
               if isinstance(item, dict) and item.get("name") == branch_name]
    if len(matches) != 1 or not SAFE_ID.fullmatch(str(matches[0].get("id", ""))):
        raise ValueError("Requested Neon branch not found or ambiguous; check NEON_BRANCH_NAME")
    branch_id = matches[0]["id"]
    databases = _get(s, project_path + f"/branches/{branch_id}/databases",
                     api_key).get("databases")
    if not isinstance(databases, list):
        raise ValueError("Neon response did not contain databases")
    if database_name:
        choices = [x for x in databases if isinstance(x, dict)
                   and x.get("name") == database_name]
    else:
        choices = [x for x in databases if isinstance(x, dict)]
        if len(choices) > 1:
            # Avoid selecting an arbitrary database or reading a protected one.
            choices = [x for x in choices if x.get("name") == "neondb"]
    if len(choices) != 1:
        raise ValueError("Neon database selection ambiguous; set NEON_DATABASE_NAME")
    chosen = choices[0]
    name, role = chosen.get("name"), chosen.get("owner_name")
    if not isinstance(name, str) or not name or not isinstance(role, str) or not role:
        raise ValueError("Neon database has no discoverable owner role")
    connection = _get(s, project_path + "/connection_uri", api_key,
                      params={"branch_id": branch_id, "database_name": name,
                              "role_name": role, "pooled": "false"}).get("uri")
    if not isinstance(connection, str) or not connection.startswith(
            ("postgres://", "postgresql://")):
        raise ValueError("Neon returned no valid PostgreSQL URI")
    # Credential-safe parser validation before passing to runner.
    from src.cloud_store import engine_for
    engine = engine_for(connection)
    engine.dispose()
    return {"uri": connection, "project_id": project_id,
            "branch": branch_name, "database_name": name, "role_name": role}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--export-github-env", action="store_true",
                   help="Mask the credential and write it to GITHUB_ENV for later steps")
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
                raise ValueError("GITHUB_ENV is absent: run this option only in Actions")
            # Mask both URI and password before using this URI later in the job.
            from sqlalchemy.engine import make_url
            raw = result["uri"]
            password = make_url(raw).password
            if password:
                print("::add-mask::" + password, flush=True)
            print("::add-mask::" + raw, flush=True)
            with Path(target).open("a", encoding="utf-8") as f:
                f.write("DATABASE_WRITE_URL=" + raw + "\n")
        print("Neon Postgres credentials resolved privately for selected branch; no URI disclosed.")
    except (ValueError, RuntimeError, OSError):
        p.exit(2, "Neon connection discovery failed. Check project secret, branch, "
                   "database and Neon API permissions; no credentials printed.\n")


if __name__ == "__main__":
    main()
