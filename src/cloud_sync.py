"""Opt-in, free-tier-conscious mirror from live APIs into hosted PostgreSQL.

The GitHub Actions runner uses a temporary SQLite staging database and never
publishes source credentials, raw XML, or a database dump as an artifact.
The hosted database is writeable ONLY from the scheduled collector.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory

from src.cloud_store import collect_sqlite_rows, engine_for, mirror
from src.db import ROOT, connect
from src.ingest.manual_grid_scope import ingest
from src.sync_context import sync
from src.schema import utc


def verify_day(records, day):
    """Fail closed if the observed daily feed has missing/overlapping intervals.

    A01 and A03 may have different counts, so verify actual source-described
    continuous interval coverage instead of requiring 96 ENTSO-E points.
    Fingrid 124/74 are strictly 96 quarter-hour records per UTC day.
    """
    start = datetime.combine(day, datetime.min.time(), timezone.utc)
    end = start + timedelta(days=1)
    streams = defaultdict(list)
    for row in records:
        a = datetime.fromisoformat(row["timestamp_utc"].replace("Z","+00:00"))
        b = datetime.fromisoformat(row["interval_end_utc"].replace("Z","+00:00"))
        key = (row["source"],row["dataset_id"],row["metric"],row["area"])
        if not start <= a < b <= end:
            raise ValueError("Source interval crosses outside verified UTC day")
        streams[key].append((a,b))
    required = {("fingrid","124","electricity_consumption","FI"),
                ("fingrid","74","electricity_production","FI"),
                ("entsoe","A65","electricity_consumption","FI")}
    if set(streams) != required:
        raise ValueError("Incomplete or unexpected verified national operational feeds")
    for key, values in streams.items():
        values.sort()
        cursor = start
        for a,b in values:
            if a != cursor:
                raise ValueError("Gap/overlap in validated national operational day")
            if key[0] == "fingrid" and b-a != timedelta(minutes=15):
                raise ValueError("Expected 15-minute Fingrid record")
            cursor = b
        if cursor != end:
            raise ValueError("Incomplete end-of-day national operational coverage")
        if key[0] == "fingrid" and len(values) != 96:
            raise ValueError("Fingrid completed UTC day must contain 96 intervals")
    return {":".join(key[:3]):len(values) for key,values in streams.items()}


def run(*, day="", backfill_days=1, url=None, today=None, syncer=sync,
        writer=mirror, engine_factory=engine_for):
    if type(backfill_days) is not int or not 1 <= backfill_days <= 7:
        raise ValueError("Limit historical batch to 1–7 completed days")
    today = today or datetime.now(timezone.utc).date()
    if day:
        target = date.fromisoformat(day)
    else:
        target = today - timedelta(days=3)
    if target > today - timedelta(days=2):
        raise ValueError("Select a fully published UTC day at least two days old")
    connection = url or os.getenv("DATABASE_WRITE_URL")
    if not connection:
        raise ValueError("DATABASE_WRITE_URL is not configured as a private secret")
    # All downloads and structural coverage checks precede remote persistence.
    days = [target - timedelta(days=i) for i in reversed(range(backfill_days))]
    with TemporaryDirectory(prefix="grid-evidence-hosted-") as folder:
        local_db = Path(folder) / "staged.sqlite"
        ingest(ROOT / "data/manual", local_db)
        observed_counts = {}
        for selected in days:
            syncer(day=selected.isoformat(), scope="both", db=local_db, today=today,
                   include_generation=False)  # A75 still needs separate live validation
            with connect(local_db) as conn:
                rows = [dict(r) for r in conn.execute(
                    "SELECT * FROM operational_series WHERE "
                    "timestamp_utc >= ? AND timestamp_utc < ?",
                    (utc(selected.isoformat()+"T00:00:00Z"),
                     utc((selected + timedelta(days=1)).isoformat()+"T00:00:00Z")))]
            observed_counts[selected.isoformat()] = verify_day(rows, selected)
        with connect(local_db) as conn:
            batches = collect_sqlite_rows(conn)
        # Commit all source categories, data revisions and all days atomically.
        engine = engine_factory(connection)
        try:
            summary = writer(engine, batches)
        finally:
            engine.dispose()
    return {
        "status": "hosted_postgres_mirror_completed",
        "days": [d.isoformat() for d in days],
        "validated_interval_counts": observed_counts,
        "table_counts": summary,
        "capacity_independently_verified": False,
        "sources": "Fingrid 124/74, ENTSO-E A65; no A75 generation",
        "note": "Observed data is delayed by upstream publication; not instantaneous telemetry",
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--day", default="", help="Latest completed UTC day, default 3 days ago")
    p.add_argument("--backfill-days", type=int, default=1, help="Range 1..7, inclusive")
    args=p.parse_args(argv)
    try:
        print(json.dumps(run(day=args.day,backfill_days=args.backfill_days),indent=2))
    except Exception:
        # Driver errors may contain connection strings; NEVER print exception
        # text in public GitHub logs. Debug using local redacted logs only.
        p.exit(2,"Hosted import failed. Check secrets, API availability, date coverage and database state; no credentials were logged.\n")


if __name__ == "__main__":
    main()
