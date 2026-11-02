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

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.ingest.http import SourceError
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


class HostedImportError(RuntimeError):
    """Only sanitized day, fixed pipeline stage and error code may reach public CI."""

    def __init__(self, day, stage, code):
        self.day, self.stage, self.code = day, stage, code
        super().__init__(f"{day}: {stage}: {code}")


def _safe_failure_code(exc):
    """Never interpolate upstream/driver exceptions: they may contain credentials."""
    if isinstance(exc, SourceError):
        # SourceError originates in our credential-safe HTTP and validation code.
        message = str(exc).lower()
        if "rejected credentials" in message:
            return "UPSTREAM_AUTH"
        if "429" in message or "retry delay" in message:
            return "UPSTREAM_RATE_LIMIT"
        if "acknowledgement" in message:
            return "UPSTREAM_ACKNOWLEDGEMENT"
        if "http " in message:
            return "UPSTREAM_HTTP"
        if "no " in message and "records" in message:
            return "UPSTREAM_EMPTY"
        return "UPSTREAM_NETWORK_OR_SOURCE"
    if isinstance(exc, (ValueError, KeyError, TypeError)):
        return "INVALID_SOURCE_SCHEMA_OR_DAY_COVERAGE"
    if isinstance(exc, (SQLAlchemyError, sqlite3.Error)):
        return "DATABASE_OR_STAGING"
    return "UNCLASSIFIED"


def _verified_existing_days(engine, days):
    """Skip only *fully* valid stored UTC days in rolling recovery.

    Read the last ten days through the database writer's private connection.
    An incomplete prior write is never treated as a complete day.
    """
    if not days:
        return set()
    with engine.connect() as db:
        if db.execute(text("SELECT to_regclass('public.latest_operational')")).scalar_one() is None:
            return set()
        records = db.execute(text(
            "SELECT source,dataset_id,metric,area,timestamp_utc,interval_end_utc "
            "FROM latest_operational WHERE timestamp_utc >= :start "
            "AND timestamp_utc < :end"
        ), {
            "start": utc(days[0].isoformat() + "T00:00:00Z"),
            "end": utc((days[-1] + timedelta(days=1)).isoformat() + "T00:00:00Z"),
        }).mappings().all()
    grouped = defaultdict(list)
    for record in records:
        grouped[record["timestamp_utc"][:10]].append(record)
    complete = set()
    for day in days:
        try:
            verify_day(grouped[day.isoformat()], day)
        except ValueError:
            continue
        complete.add(day)
    return complete


def run(*, day="", backfill_days=1, recover_days=1, url=None, today=None,
        syncer=sync, writer=mirror, engine_factory=engine_for):
    if type(backfill_days) is not int or not 1 <= backfill_days <= 7:
        raise ValueError("Limit historical batch to 1–7 completed days")
    if type(recover_days) is not int or not 1 <= recover_days <= 10:
        raise ValueError("Limit rolling recovery to 1–10 completed days")
    if recover_days > 1 and backfill_days != 1:
        raise ValueError("Select either manual backfill or rolling recovery")
    today = today or datetime.now(timezone.utc).date()
    target = date.fromisoformat(day) if day else today - timedelta(days=3)
    if target > today - timedelta(days=2):
        raise ValueError("Select a fully published UTC day at least two days old")
    connection = url or os.getenv("DATABASE_WRITE_URL")
    if not connection:
        raise ValueError("DATABASE_WRITE_URL is not configured as a private secret")

    recovery = recover_days > 1
    count = recover_days if recovery else backfill_days
    days = [target - timedelta(days=i) for i in reversed(range(count))]
    stage = ["STAGING"]
    def update_stage(name):
        stage[0] = name

    def prepare_day(selected, local_db):
        stage[0] = "LOAD_MANUAL_EVIDENCE"
        try:
            ingest(ROOT / "data/manual", local_db)
            stage[0] = "SOURCE_FETCH"
            kwargs = {}
            if syncer is sync:
                kwargs["on_stage"] = update_stage
            syncer(day=selected.isoformat(), scope="both", db=local_db,
                   today=today, include_generation=False, **kwargs)
            stage[0] = "VERIFY_UTC_DAY"
            with connect(local_db) as conn:
                records = [dict(r) for r in conn.execute(
                    "SELECT * FROM operational_series WHERE "
                    "timestamp_utc >= ? AND timestamp_utc < ?",
                    (utc(selected.isoformat()+"T00:00:00Z"),
                     utc((selected + timedelta(days=1)).isoformat()+"T00:00:00Z")))]
                counts = verify_day(records, selected)
                batches = collect_sqlite_rows(conn)
            return counts, batches
        except Exception as exc:
            raise HostedImportError(selected.isoformat(), stage[0],
                                    _safe_failure_code(exc)) from None

    try:
        engine = engine_factory(connection)
    except Exception as exc:
        raise HostedImportError(target.isoformat(), "DATABASE_CONFIGURATION",
                                _safe_failure_code(exc)) from None
    try:
        try:
            already_complete = _verified_existing_days(engine, days) if recovery else set()
        except Exception as exc:
            raise HostedImportError(target.isoformat(), "DATABASE_RECOVERY_READ",
                                    _safe_failure_code(exc)) from None
        observed_counts, failed, batches = {}, [], None
        with TemporaryDirectory(prefix="grid-evidence-hosted-") as folder:
            for selected in days:
                if selected in already_complete:
                    continue
                # Isolated staging prevents an invalid day from contaminating
                # a valid day in the same recovery batch.
                local_db = Path(folder) / (selected.isoformat() + ".sqlite")
                try:
                    counts, day_rows = prepare_day(selected, local_db)
                except HostedImportError as exc:
                    if not recovery:
                        raise
                    failed.append({"day": exc.day, "stage": exc.stage, "code": exc.code})
                    continue
                observed_counts[selected.isoformat()] = counts
                if batches is None:
                    batches = day_rows
                else:
                    batches["operational_series"].extend(day_rows["operational_series"])
            if batches is None and not already_complete:
                last = failed[-1]
                raise HostedImportError(last["day"], last["stage"], last["code"])
            summary = {}
            if batches is not None:
                try:
                    summary = writer(engine, batches)
                except Exception as exc:
                    raise HostedImportError(target.isoformat(), "POSTGRES_MIRROR",
                                            _safe_failure_code(exc)) from None
        if failed:
            for item in failed:
                # Fixed stage and error code only; never raw HTTP or driver text.
                print(f"::warning::Missing verified UTC day {item['day']}: "
                      f"{item['stage']} / {item['code']}", flush=True)
        return {
            "status": ("hosted_postgres_mirror_partial" if failed else
                       "hosted_postgres_mirror_completed"),
            "days": [d.isoformat() for d in days],
            "newly_validated_days": sorted(observed_counts),
            "already_complete_days": sorted(d.isoformat() for d in already_complete),
            "failed_days": failed,
            "validated_interval_counts": observed_counts,
            "table_counts": summary,
            "capacity_independently_verified": False,
            "sources": "Fingrid 124/74, ENTSO-E A65; no A75 generation",
            "note": "Observed data is delayed by upstream publication; not instantaneous telemetry",
        }
    finally:
        engine.dispose()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--day", default="", help="Latest completed UTC day, default 3 days ago")
    p.add_argument("--backfill-days", type=int, default=1, help="Strict manual range 1..7")
    p.add_argument("--recover-days", type=int, default=1,
                   help="Rolling recovery 1..10; skip only verified existing days")
    args = p.parse_args(argv)
    try:
        print(json.dumps(run(day=args.day, backfill_days=args.backfill_days,
                             recover_days=args.recover_days), indent=2))
    except HostedImportError as exc:
        p.exit(2, f"Hosted import failed: {exc}\n")
    except Exception:
        # Driver errors can contain connection strings. Never print raw errors.
        p.exit(2, "Hosted import failed during configuration or an unexpected "
               "pipeline error; no credentials were logged.\n")


if __name__ == "__main__":
    main()
