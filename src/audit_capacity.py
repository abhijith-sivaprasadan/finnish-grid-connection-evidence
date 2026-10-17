"""Export a per-observation Grid Scope source-recheck checklist.

This prepares a human audit; it does not claim independent verification or
change the append-only public evidence observations in SQLite.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sqlite3

from src.db import connect

FIELDS = [
    "observation_id", "connection_point", "direction", "effective_year",
    "recorded_value", "recorded_unit", "source_url", "source_observed_at",
    "source_published_on", "capacity_status", "validity_notes",
    "independent_recheck_status", "rechecked_on_utc", "verified_value",
    "verified_unit", "verification_evidence_url", "review_notes",
]


def audit_rows(conn) -> list[dict]:
    result = []
    source = conn.execute("""
        SELECT o.*, p.name AS point_name
        FROM capacity_observation AS o
        JOIN connection_point AS p USING(connection_point_id)
        ORDER BY p.name, o.direction, o.effective_year, o.source_observed_at
    """)
    for r in source:
        if r["capacity_status"] != "published_indicative":
            continue  # Operator-confirmed and scenarios are distinct categories.
        result.append({
            "observation_id": r["observation_id"],
            "connection_point": r["point_name"],
            "direction": r["direction"],
            "effective_year": r["effective_year"] if r["effective_year"] is not None else "",
            "recorded_value": r["capacity_value"],
            "recorded_unit": r["capacity_unit"],
            "source_url": r["source_url"],
            "source_observed_at": r["source_observed_at"],
            "source_published_on": r["source_published_on"] or "",
            "capacity_status": r["capacity_status"],
            "validity_notes": r["validity_notes"],
            "independent_recheck_status": "pending_independent_recheck",
            "rechecked_on_utc": "",
            "verified_value": "",
            "verified_unit": "",
            "verification_evidence_url": "",
            "review_notes": "",
        })
    return result


def export_checklist(output: Path, *, db=None) -> dict:
    output = Path(output)
    with connect(db) as conn:
        records = audit_rows(conn)
    if not records:
        raise ValueError("No published indicative observations available for an audit")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Fail rather than silently overwriting a reviewer's evidence.
    with output.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    return {
        "status": "audit_checklist_created_not_independently_verified",
        "path": str(output),
        "observations_to_recheck": len(records),
        "independently_verified_by_this_command": 0,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=None, help="Local SQLite source")
    parser.add_argument("--output", type=Path,
                        default=Path("data/audit/grid_scope_recheck.csv"),
                        help="New CSV destination; refuses to overwrite an existing audit")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(export_checklist(args.output, db=args.db), indent=2))
    except (ValueError, FileExistsError, OSError, sqlite3.Error) as exc:
        parser.exit(2, f"Audit export failed: {exc}\n")


if __name__ == "__main__":
    main()
