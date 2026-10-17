"""Independent-of-importer integrity audit for local Finnish grid evidence.

Checks internally reproducible constraints. It DOES NOT independently verify
operator source values or validate physical grid connectability.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from math import isfinite
from pathlib import Path
import argparse
import csv
import json
import sqlite3
from src.db import connect, ROOT

EXPECTED = {"fingrid": {"124": ("electricity_consumption", "MWh/h"),
                        "74": ("electricity_production", "MWh/h")},
            "entsoe": {"A65": ("electricity_consumption", "MW")}}


def utc_time(value):
    value = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("Expected explicit UTC time zone")
    return parsed.astimezone(timezone.utc)


def audit(conn, *, manual_file=None):
    findings = []
    counts = {}
    def issue(code, level, detail):
        findings.append({"code": code, "severity": level, "detail": detail})
    manual_file = Path(manual_file or ROOT / "data/manual/grid_scope_observations.csv")
    observations = list(conn.execute("SELECT * FROM capacity_observation"))
    operational = list(conn.execute("SELECT * FROM latest_operational"))
    counts["capacity"] = len(observations)
    counts["operational_latest"] = len(operational)

    if not manual_file.exists():
        issue("CSV_MISSING", "blocker", "Manual Grid Scope source CSV is absent")
    else:
        with manual_file.open(encoding="utf-8-sig", newline="") as f:
            csv_records = list(csv.DictReader(f))
        ids = [r["observation_id"] for r in csv_records]
        if len(set(ids)) != len(ids):
            issue("CSV_DUPLICATE_ID", "blocker", "Manual source contains repeated observation IDs")
        by_id = {r["observation_id"]: r for r in observations}
        for record in csv_records:
            existing = by_id.get(record["observation_id"])
            if existing is None:
                issue("CSV_NOT_IMPORTED", "action", f"Missing imported record: {record['observation_id']}")
                continue
            # Compare independently parsed source strings to DB fields; this
            # is *internal provenance agreement*, not operator verification.
            fields = ("connection_point_id", "direction", "effective_year",
                      "capacity_value", "capacity_unit", "capacity_status",
                      "source_url", "source_observed_at", "validity_notes",
                      "source_published_on")
            for field in fields:
                recorded = existing[field]
                source = record.get(field, "").strip()
                if field == "effective_year":
                    correct = (None if source == "" else int(source))
                elif field == "capacity_value":
                    correct = float(source)
                else:
                    correct = None if field == "source_published_on" and not source else source
                if recorded != correct:
                    issue("CSV_DB_MISMATCH", "blocker",
                          f"{record['observation_id']} field {field} differs from committed CSV")
        counts["manual_csv_rows"] = len(csv_records)

    if not observations:
        issue("NO_CAPACITY", "action", "No imported Grid Scope capacity observations")
    for r in observations:
        if r["capacity_status"] == "operator_confirmed":
            if not r["confirmation_evidence_url"]:
                issue("UNSUPPORTED_CONFIRMATION", "blocker", "Confirmed claim has no document")
        if r["capacity_status"] == "published_indicative" and not r["validity_notes"]:
            issue("CAPACITY_CAVEAT_MISSING", "blocker", r["observation_id"])

    if not operational:
        issue("NO_PERSISTED_OPERATIONS", "action",
              "No locally persistent operational series; remote smoke runs are not local data")
    streams = defaultdict(list)
    source_counts = Counter()
    for r in operational:
        source_counts[f"{r['source']}:{r['dataset_id']}"] += 1
        origin = EXPECTED.get(r["source"], {}).get(r["dataset_id"])
        if origin and (r["metric"], r["unit"]) != origin:
            issue("METRIC_UNIT_MISMATCH", "blocker",
                  f"{r['source']}:{r['dataset_id']} unexpected metric or unit")
        if r["area"] != "FI" or r["evidence_category"] != "operational_context":
            issue("CATEGORY_LEAK", "blocker", "National operational data category or area incorrect")
        if not isfinite(r["value"]):
            issue("NONFINITE_OBSERVATION", "blocker", "Non-finite operational value")
        try:
            start, end = utc_time(r["timestamp_utc"]), utc_time(r["interval_end_utc"])
        except (ValueError, TypeError):
            issue("INVALID_UTC", "blocker", "Bad time or non-UTC interval")
            continue
        if not end > start:
            issue("NONPOSITIVE_INTERVAL", "blocker", "Zero/negative operational interval")
        streams[(r["source"],r["dataset_id"],r["metric"])].append((start,end))
    for (source,dataset,metric), intervals in streams.items():
        intervals.sort()
        for previous, current in zip(intervals,intervals[1:]):
            if current[0] < previous[1]:
                issue("OPERATIONAL_OVERLAP", "blocker",
                      f"{source}:{dataset}:{metric} overlapping source intervals")
            elif current[0] > previous[1]:
                issue("OPERATIONAL_GAP", "review",
                      f"{source}:{dataset}:{metric} source intervals have gaps")
    counts["source_counts"] = dict(source_counts)
    codes = {f["code"] for f in findings}
    passed = not any(f["severity"] == "blocker" for f in findings)
    return {"status": "internal_integrity_passed" if passed else "integrity_blocked",
            "scope": "source CSV vs SQLite and time-series structure, not operator-value verification",
            "source_values_independently_verified": False,
            "counts": counts, "findings": findings,
            "internal_integrity_passed": passed,
            "operational_rows_in_db": bool(operational),
            "authenticated_live_origin_proven_by_db_alone": False,
            "operator_value_verification_pending": True,
            "requires_action": bool(codes & {"CSV_MISSING","CSV_NOT_IMPORTED","NO_CAPACITY","NO_PERSISTED_OPERATIONS"})}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db",type=Path,default=None)
    parser.add_argument("--output",type=Path,default=None,
                        help="Optional new JSON report path (refuses overwrite)")
    args=parser.parse_args(argv)
    try:
        with connect(args.db) as db:
            result=audit(db)
        raw=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
        if args.output is not None:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            with args.output.open("x",encoding="utf-8") as f:
                f.write(raw)
        print(raw,end="")
        if not result["internal_integrity_passed"]:
            parser.exit(2)
    except (sqlite3.Error, OSError, ValueError) as ex:
        parser.exit(2, f"Integrity audit failed: {ex}\n")

if __name__=="__main__":
    main()
