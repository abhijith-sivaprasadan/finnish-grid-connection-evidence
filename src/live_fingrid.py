"""Optional Fingrid live check. No credentials, raw responses or data are published.

Supply FINGRID_API_KEY as a private environment variable or GitHub Actions secret.
Results persist only in a temporary SQLite database, which is deleted afterward.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory

from src.db import connect, insert
from src.ingest.fingrid import DATASETS, fetch
from src.ingest.http import SourceError
from src.live_entsoe import completed_utc_day

KINDS = {"consumption": (124,), "production": (74,), "both": (124, 74)}


def live_smoke(*, day: str = "", kind: str = "both", getter=None, today=None) -> dict:
    start, end = completed_utc_day(day, today=today)
    if kind not in KINDS:
        raise ValueError("Use consumption, production or both")
    if not os.environ.get("FINGRID_API_KEY"):
        raise SourceError("Set FINGRID_API_KEY privately; see docs/FINGRID_LIVE.md")

    get = getter or fetch
    window_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
    window_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
    counts = Counter()
    with TemporaryDirectory(prefix="fingrid-check-") as folder:
        with connect(Path(folder) / "evidence.sqlite") as conn:
            for dataset_id in KINDS[kind]:
                records = get(dataset_id, start, end)
                if not records:
                    raise SourceError(
                        f"No Fingrid observations returned for dataset {dataset_id}; "
                        "check publication timing or the requested day"
                    )
                metric, unit = DATASETS[dataset_id]
                for record in records:
                    if (record.source != "fingrid" or record.area != "FI"
                            or record.dataset_id != str(dataset_id)
                            or record.metric != metric or record.unit != unit):
                        raise ValueError("Unexpected source/dataset/unit in Fingrid response")
                    timestamp = datetime.fromisoformat(record.timestamp_utc.replace("Z", "+00:00"))
                    if not (window_start <= timestamp < window_end):
                        raise ValueError("Fingrid response timestamp is outside requested day")
                    if not insert(conn, record):
                        raise ValueError("Duplicate Fingrid observation in source response")
                    counts[str(dataset_id)] += 1
            persisted = conn.execute("SELECT count(*) FROM operational_series").fetchone()[0]
            capacity = conn.execute("SELECT count(*) FROM capacity_observation").fetchone()[0]
            if persisted != sum(counts.values()) or capacity != 0:
                raise ValueError("Fingrid temporary operational-data persistence check failed")
    return {
        "status": "authenticated_source_parse_and_temporary_db_insert_passed",
        "source": "Fingrid Open Data",
        "country": "Finland",
        "dataset_ids": list(counts),
        "window_start_utc": start,
        "window_end_utc": end,
        "records_by_dataset": dict(counts),
        "records": persisted,
        "source_units": {str(dataset_id): DATASETS[dataset_id][1] for dataset_id in KINDS[kind]},
        "scope": "national operational context only; not substation connection capacity",
        "persistence": "temporary database deleted after check",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day", default="", help="UTC YYYY-MM-DD (default: three days ago)")
    parser.add_argument("--kind", choices=sorted(KINDS), default="both")
    args = parser.parse_args(argv)
    try:
        result = live_smoke(day=args.day, kind=args.kind)
    except (ValueError, OSError, sqlite3.Error, SourceError) as exc:
        parser.exit(2, f"Fingrid live check failed: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
