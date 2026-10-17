"""Persist verified Finland-wide operational context in the local SQLite database.

This is an *opt-in local command*, not a GitHub Actions job: credentials remain in
process environment variables and raw third-party data are never committed.
All requested datasets are fetched and validated before one atomic DB transaction.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
import os
from pathlib import Path
import sqlite3

from src.db import connect, db_path, insert
from src.ingest.entsoe import fetch as fetch_entsoe
from src.ingest.fingrid import DATASETS, fetch as fetch_fingrid
from src.ingest.http import SourceError
from src.live_entsoe import completed_utc_day
from src.quality import report

SCOPES = ("both", "fingrid", "entsoe")


def _expect(records, *, source, dataset_id, metric=None, unit, start, end):
    if not records:
        raise SourceError(f"No {source} {dataset_id} records for selected UTC day")
    first = datetime.fromisoformat(start.replace("Z", "+00:00"))
    last = datetime.fromisoformat(end.replace("Z", "+00:00"))
    for record in records:
        if (record.source != source or record.area != "FI"
                or record.dataset_id != dataset_id or record.unit != unit
                or (metric is not None and record.metric != metric)):
            raise ValueError(f"Unexpected {source} {dataset_id} record identity or units")
        if source == "entsoe" and dataset_id == "A75" and not (
                record.metric.startswith("generation_")
                and record.metric.endswith("_production")):
            raise ValueError("ENTSO-E A75 metrics must retain generation type and production direction")
        timestamp = datetime.fromisoformat(record.timestamp_utc.replace("Z", "+00:00"))
        endtime = datetime.fromisoformat(record.interval_end_utc.replace("Z", "+00:00"))
        if not (first <= timestamp < endtime <= last):
            raise ValueError(f"{source} {dataset_id} record falls outside completed-day window")


def sync(day="", *, scope="both", db=None, include_generation=False,
         fingrid_getter=None, entsoe_getter=None, today=None):
    """Retrieve real data before writing any row. Return safe aggregate metadata."""
    start, end = completed_utc_day(day, today=today)
    if scope not in SCOPES:
        raise ValueError("scope must be both, fingrid or entsoe")
    if include_generation and scope == "fingrid":
        raise ValueError("ENTSO-E generation requires scope both or entsoe")
    do_fingrid = scope in {"both", "fingrid"}
    do_entsoe = scope in {"both", "entsoe"}
    missing = []
    if do_fingrid and not os.environ.get("FINGRID_API_KEY"):
        missing.append("FINGRID_API_KEY")
    if do_entsoe and not os.environ.get("ENTSOE_API_TOKEN"):
        missing.append("ENTSOE_API_TOKEN")
    if missing:
        raise SourceError("Missing private environment variable(s): " + ", ".join(missing))

    fg = fingrid_getter or fetch_fingrid
    ee = entsoe_getter or fetch_entsoe
    rows = []
    source_counts = Counter()

    if do_fingrid:
        for dataset_id in (124, 74):
            metric, unit = DATASETS[dataset_id]
            fetched = fg(dataset_id, start, end)
            _expect(fetched, source="fingrid", dataset_id=str(dataset_id),
                    metric=metric, unit=unit, start=start, end=end)
            source_counts[f"fingrid:{dataset_id}"] = len(fetched)
            rows.extend(fetched)

    if do_entsoe:
        for kind in (("load", "generation") if include_generation else ("load",)):
            fetched = ee(kind, start, end)
            dataset_id = {"load": "A65", "generation": "A75"}[kind]
            metric = "electricity_consumption" if kind == "load" else None
            _expect(fetched, source="entsoe", dataset_id=dataset_id,
                    metric=metric, unit="MW", start=start, end=end)
            source_counts[f"entsoe:{kind}"] = len(fetched)
            rows.extend(fetched)

    # One exact source snapshot must never contain the same observation twice.
    identities = [
        (r.source, r.dataset_id, r.metric, r.area,
         r.timestamp_utc, r.interval_end_utc, r.retrieved_at) for r in rows
    ]
    if len(set(identities)) != len(identities):
        raise ValueError("Duplicate records in source responses; database not changed")

    target = db_path(db)
    with connect(target) as conn:
        # Connection manager rolls back every operation if any insert fails.
        inserted = sum(insert(conn, row) for row in rows)
        quality = report(conn)
    return {
        "status": "local_operational_context_persisted",
        "utc_window": {"start": start, "end": end},
        "data_file": str(target),
        "records_retrieved": len(rows),
        "new_revision_rows": inserted,
        "records_by_source": dict(source_counts),
        "quality": quality,
        "warning": "National operational data only; not available connection capacity",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day", default="", help="Completed UTC date YYYY-MM-DD; default three days ago")
    parser.add_argument("--scope", choices=SCOPES, default="both")
    parser.add_argument("--db", type=Path, default=None, help="Local SQLite destination (default data/evidence.sqlite)")
    parser.add_argument("--include-generation", action="store_true",
                        help="Also ingest ENTSO-E A75; use only after separate generation smoke succeeds")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(sync(args.day, scope=args.scope, db=args.db,
                              include_generation=args.include_generation), indent=2))
    except (SourceError, ValueError, OSError, sqlite3.Error, KeyError, TypeError) as exc:
        parser.exit(2, f"Context import failed: {exc}\n")


if __name__ == "__main__":
    main()
