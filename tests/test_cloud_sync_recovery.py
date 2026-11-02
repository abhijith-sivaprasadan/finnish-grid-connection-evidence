"""Scheduled recovery contracts: never invent intervals or expose credentials."""
from datetime import date, datetime, timedelta, timezone

import pytest

from src import cloud_sync
from src.db import connect, insert
from src.ingest.http import SourceError
from src.schema import OperationalRecord


class FakeEngine:
    def __init__(self):
        self.disposed = False

    def dispose(self):
        self.disposed = True


def populate_complete_day(day, db):
    start = datetime.combine(date.fromisoformat(day), datetime.min.time(), timezone.utc)
    with connect(db) as conn:
        for source, dataset, metric, unit in (
            ("fingrid", "124", "electricity_consumption", "MWh/h"),
            ("fingrid", "74", "electricity_production", "MWh/h"),
            ("entsoe", "A65", "electricity_consumption", "MW"),
        ):
            for n in range(96):
                a = start + timedelta(minutes=15*n)
                b = a + timedelta(minutes=15)
                insert(conn, OperationalRecord(
                    source=source, dataset_id=dataset, metric=metric, unit=unit,
                    value=8000.0, timestamp_utc=a.isoformat(),
                    interval_end_utc=b.isoformat(), retrieved_at="2026-11-02T00:00:00Z",
                    source_url=("https://data.fingrid.fi/en/datasets/" + dataset
                                if source == "fingrid" else "https://transparency.entsoe.eu/"),
                ))


def test_recovery_isolates_bad_day_and_skips_complete_day(monkeypatch):
    engine = FakeEngine()
    seen, uploads = [], []

    def syncer(*, day, scope, db, today, include_generation):
        seen.append(day)
        if day == "2026-10-29":
            raise SourceError("Source returned HTTP 429; no records imported")
        populate_complete_day(day, db)

    def writer(_, batches):
        uploads.append(batches)
        return {"operational_series": {"submitted": len(batches["operational_series"])}}

    monkeypatch.setattr(cloud_sync, "_verified_existing_days",
                        lambda _engine, _days: {date(2026, 10, 28)})
    result = cloud_sync.run(
        day="2026-10-30", today=date(2026, 11, 2), recover_days=3,
        url="postgresql://dummy.invalid/no-secrets", syncer=syncer,
        engine_factory=lambda _: engine, writer=writer)
    assert result["status"] == "hosted_postgres_mirror_partial"
    assert result["newly_validated_days"] == ["2026-10-30"]
    assert result["already_complete_days"] == ["2026-10-28"]
    assert result["failed_days"] == [{
        "day": "2026-10-29", "stage": "SOURCE_FETCH", "code": "UPSTREAM_RATE_LIMIT"}]
    assert seen == ["2026-10-29", "2026-10-30"]
    assert len(uploads) == 1
    assert len(uploads[0]["operational_series"]) == 288
    assert all(row["timestamp_utc"].startswith("2026-10-30")
               for row in uploads[0]["operational_series"])
    assert engine.disposed


def test_strict_manual_backfill_rejects_failure_without_partial_mirror():
    engine = FakeEngine()
    uploads = []

    def syncer(*, day, scope, db, today, include_generation):
        if day == "2026-10-29":
            raise SourceError("Source returned HTTP 500; no records imported")
        populate_complete_day(day, db)

    with pytest.raises(cloud_sync.HostedImportError, match="UPSTREAM_HTTP"):
        cloud_sync.run(
            day="2026-10-30", today=date(2026, 11, 2), backfill_days=2,
            url="postgresql://dummy.invalid/no-secrets", syncer=syncer,
            engine_factory=lambda _: engine,
            writer=lambda *args: uploads.append(args))
    assert uploads == []
    assert engine.disposed


def test_error_redaction_including_database_exception():
    engine = FakeEngine()
    sensitive = "postgresql://user:my-password@example.org/secret"

    def syncer(**kwargs):
        raise RuntimeError("unexpected provider response " + sensitive)

    with pytest.raises(cloud_sync.HostedImportError) as caught:
        cloud_sync.run(
            day="2026-10-30", today=date(2026, 11, 2),
            url="postgresql://dummy.invalid/no-secrets",
            syncer=syncer, engine_factory=lambda _: engine)
    message = str(caught.value)
    assert "my-password" not in message
    assert "example.org" not in message
    assert "UNCLASSIFIED" in message
    assert engine.disposed


def test_recovery_day_count_and_manual_backfill_are_mutually_exclusive():
    with pytest.raises(ValueError, match="either manual backfill or rolling recovery"):
        cloud_sync.run(backfill_days=3, recover_days=10, today=date(2026, 11, 2))
    with pytest.raises(ValueError, match="rolling recovery"):
        cloud_sync.run(recover_days=11, today=date(2026, 11, 2))


def test_all_failed_recovery_must_not_report_green_with_existing_older_day(monkeypatch):
    engine = FakeEngine()
    calls = []
    monkeypatch.setattr(cloud_sync, "_verified_existing_days",
                        lambda _engine, _days: {date(2026, 10, 28)})

    def syncer(*, day, scope, db, today, include_generation):
        calls.append(day)
        raise SourceError("Source rejected credentials; check your API subscription and key")

    with pytest.raises(cloud_sync.HostedImportError,
                       match="2026-10-30: SOURCE_FETCH: UPSTREAM_AUTH"):
        cloud_sync.run(
            day="2026-10-30", today=date(2026, 11, 2), recover_days=3,
            url="postgresql://dummy.invalid/no-secrets", syncer=syncer,
            engine_factory=lambda _: engine)
    assert calls == ["2026-10-29", "2026-10-30"]
    assert engine.disposed


def test_partial_backfill_still_imports_valid_older_day_but_reports_failure(monkeypatch):
    engine = FakeEngine()
    uploads = []
    monkeypatch.setattr(cloud_sync, "_verified_existing_days",
                        lambda _engine, _days: set())

    def syncer(*, day, scope, db, today, include_generation):
        if day == "2026-10-30":
            raise SourceError("Source rejected credentials; check your API subscription and key")
        populate_complete_day(day, db)

    with pytest.raises(cloud_sync.HostedImportError,
                       match="2026-10-30: SOURCE_FETCH: UPSTREAM_AUTH"):
        cloud_sync.run(
            day="2026-10-30", today=date(2026, 11, 2), recover_days=2,
            url="postgresql://dummy.invalid/no-secrets", syncer=syncer,
            engine_factory=lambda _: engine,
            writer=lambda _, batches: uploads.append(batches) or {"ok": True})
    assert len(uploads) == 1
    assert len(uploads[0]["operational_series"]) == 288
    assert all(row["timestamp_utc"].startswith("2026-10-29")
               for row in uploads[0]["operational_series"])
    assert engine.disposed
