"""Opt-in authenticated ENTSO-E smoke run; never prints credentials or full URLs.

Use locally after setting ENTSOE_API_TOKEN, or run the manual GitHub Actions
workflow with a repository secret of the same name. No data is committed.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from src.db import connect, insert
from src.ingest.entsoe import fetch
from src.ingest.http import SourceError


def completed_utc_day(raw: str = "", *, today: date | None = None) -> tuple[str, str]:
    today = today or datetime.now(timezone.utc).date()
    if raw:
        try:
            day = date.fromisoformat(raw)
        except ValueError:
            raise ValueError("Provide an ISO date YYYY-MM-DD") from None
        if day.isoformat() != raw:
            raise ValueError("Provide an ISO date YYYY-MM-DD")
    else:
        day = today - timedelta(days=3)
    if day > today - timedelta(days=2):
        raise ValueError("Choose a completed UTC day at least two days in the past")
    return day.isoformat() + "T00:00:00Z", (day + timedelta(days=1)).isoformat() + "T00:00:00Z"


def live_smoke(*, day: str = "", kind: str = "load", getter=None, today: date | None = None) -> dict:
    start, end = completed_utc_day(day, today=today)
    if kind not in {"load", "generation"}:
        raise ValueError("Only load or generation smoke checks are supported")
    if not os.environ.get("ENTSOE_API_TOKEN"):
        raise SourceError("Set ENTSOE_API_TOKEN privately before live requests")
    records = (getter or fetch)(kind, start, end)
    if not records:
        raise SourceError("No time-series observations were returned for the selected day")
    with TemporaryDirectory(prefix="entsoe-check-") as folder:
        with connect(Path(folder) / "evidence.sqlite") as conn:
            inserted = sum(insert(conn, rec) for rec in records)
            sources = {row[0] for row in conn.execute("SELECT DISTINCT source FROM operational_series")}
            if sources != {"entsoe"} or inserted != len(records):
                raise ValueError("ENTSO-E operational-context persistence check failed")
            metrics = sorted({row[0] for row in conn.execute("SELECT DISTINCT metric FROM operational_series")})
    return {
        "status": "authenticated_source_parse_and_temporary_db_insert_passed",
        "source": "ENTSO-E Transparency Platform",
        "country": "Finland",
        "kind": kind,
        "window_start_utc": start,
        "window_end_utc": end,
        "records": len(records),
        "inserted": inserted,
        "metrics": metrics,
        "scope": "national operational context only; not grid-connection capacity",
        "persistence": "temporary database deleted after check",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day", default="", help="UTC date YYYY-MM-DD (default: three days ago)")
    parser.add_argument("--kind", choices=["load", "generation"], default="load")
    args = parser.parse_args(argv)
    try:
        result = live_smoke(day=args.day, kind=args.kind)
    except (SourceError, ValueError, OSError) as exc:
        parser.exit(2, f"ENTSO-E live check failed: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
