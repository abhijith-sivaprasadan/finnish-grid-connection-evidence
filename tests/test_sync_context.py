"""No network: synthetic records exercise atomic local persistence."""
from datetime import date
import os
import pytest

from src.db import connect, insert, ROOT
from src.ingest.manual_grid_scope import ingest
from src.schema import OperationalRecord
from src import sync_context

TODAY = date(2026, 10, 17)
DAY = "2026-10-14"
STAMP = "2026-10-17T00:00:00Z"


def record(source, dataset, metric, unit, value, *, retrieved_at=STAMP):
    return OperationalRecord(
        source=source, dataset_id=dataset, metric=metric, unit=unit,
        value=value, timestamp_utc="2026-10-14T00:00:00Z",
        interval_end_utc="2026-10-14T00:15:00Z",
        retrieved_at=retrieved_at,
        source_url=("https://data.fingrid.fi/en/datasets/" + dataset
                    if source == "fingrid" else "https://transparency.entsoe.eu/"),
    )


def fixtures():
    return [
        record("fingrid", "124", "electricity_consumption", "MWh/h", 8000),
        record("fingrid", "74", "electricity_production", "MWh/h", 7600),
        record("entsoe", "A65", "electricity_consumption", "MW", 7980),
    ]


def mock_fetchers(values=None):
    rows = values or fixtures()
    return (
        lambda dataset_id, start, end: [r for r in rows
                                      if r.source == "fingrid" and r.dataset_id == str(dataset_id)],
        lambda kind, start, end: [r for r in rows
                                 if r.source == "entsoe"
                                 and r.dataset_id == ("A65" if kind == "load" else "A75")]
    )


def test_both_sources_persist_into_local_dashboard_db(tmp_path, monkeypatch):
    monkeypatch.setenv("FINGRID_API_KEY", "TEST_KEY")
    monkeypatch.setenv("ENTSOE_API_TOKEN", "TEST_TOKEN")
    path = tmp_path / "evidence.sqlite"
    ingest(ROOT / "data" / "manual", path)
    fg, ee = mock_fetchers()
    result = sync_context.sync(DAY, db=path, today=TODAY,
                               fingrid_getter=fg, entsoe_getter=ee)
    assert result["new_revision_rows"] == 3
    assert result["records_retrieved"] == 3
    assert result["quality"]["mvp_data_ready"] is True
    assert result["records_by_source"] == {"fingrid:124": 1, "fingrid:74": 1, "entsoe:load": 1}
    with connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM latest_operational").fetchone()[0] == 3
        assert conn.execute("SELECT count(*) FROM published_capacity").fetchone()[0] == 18
        assert conn.execute("SELECT count(*) FROM capacity_observation WHERE capacity_status='operator_confirmed'").fetchone()[0] == 0
    # Repeating exact fetched snapshot is idempotent, and does not overwrite records.
    repeat = sync_context.sync(DAY, db=path, today=TODAY,
                               fingrid_getter=fg, entsoe_getter=ee)
    assert repeat["new_revision_rows"] == 0


def test_failed_second_fetch_does_not_modify_existing_database(tmp_path, monkeypatch):
    monkeypatch.setenv("FINGRID_API_KEY", "TEST_KEY")
    monkeypatch.setenv("ENTSOE_API_TOKEN", "TEST_TOKEN")
    path = tmp_path / "evidence.sqlite"
    with connect(path) as conn:
        insert(conn, fixtures()[0])
    fg, _ = mock_fetchers()
    with pytest.raises(Exception, match="No entsoe A65"):
        sync_context.sync(DAY, db=path, today=TODAY,
                          fingrid_getter=fg, entsoe_getter=lambda *args: [])
    with connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM operational_series").fetchone()[0] == 1


def test_transaction_rolls_back_earlier_inserts_if_later_record_conflicts(tmp_path, monkeypatch):
    monkeypatch.setenv("FINGRID_API_KEY", "TEST_KEY")
    monkeypatch.setenv("ENTSOE_API_TOKEN", "TEST_TOKEN")
    path = tmp_path / "evidence.sqlite"
    baseline = fixtures()[2]
    with connect(path) as conn:
        insert(conn, baseline)
    alternate = record("entsoe", "A65", "electricity_consumption", "MW", 1234)
    fg, ee = mock_fetchers([fixtures()[0], fixtures()[1], alternate])
    with pytest.raises(ValueError, match="Conflicting operational revision"):
        sync_context.sync(DAY, db=path, today=TODAY, fingrid_getter=fg, entsoe_getter=ee)
    with connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM operational_series").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM operational_series WHERE source='fingrid'").fetchone()[0] == 0


def test_missing_one_of_two_secrets_fails_before_network_or_db(tmp_path, monkeypatch):
    monkeypatch.setenv("FINGRID_API_KEY", "TEST_KEY")
    monkeypatch.delenv("ENTSOE_API_TOKEN", raising=False)
    path = tmp_path / "evidence.sqlite"
    def never(*args):
        raise AssertionError("Should not fetch without all required secrets")
    with pytest.raises(Exception, match="ENTSOE_API_TOKEN"):
        sync_context.sync(DAY, db=path, today=TODAY,
                          fingrid_getter=never, entsoe_getter=never)
    assert not path.exists()


@pytest.mark.parametrize("scope", ["fingrid", "entsoe"])
def test_single_source_uses_only_its_own_secret(tmp_path, monkeypatch, scope):
    monkeypatch.setenv("FINGRID_API_KEY", "TEST_KEY")
    monkeypatch.setenv("ENTSOE_API_TOKEN", "TEST_TOKEN")
    fg, ee = mock_fetchers()
    result = sync_context.sync(DAY, db=tmp_path / "db", scope=scope,
                               today=TODAY, fingrid_getter=fg, entsoe_getter=ee)
    assert result["new_revision_rows"] == (2 if scope == "fingrid" else 1)


def test_wrong_source_identity_rejected_before_db_write(tmp_path, monkeypatch):
    monkeypatch.setenv("FINGRID_API_KEY", "TEST_KEY")
    path = tmp_path / "db"
    with pytest.raises(ValueError, match="record identity or units"):
        sync_context.sync(DAY, db=path, scope="fingrid", today=TODAY,
            fingrid_getter=lambda *args: [fixtures()[2]])
    assert not path.exists()


def test_day_window_validation_before_fetch(tmp_path, monkeypatch):
    monkeypatch.setenv("FINGRID_API_KEY", "TEST_KEY")
    with pytest.raises(ValueError, match="two days in the past"):
        sync_context.sync("2026-10-17", scope="fingrid", db=tmp_path / "db", today=TODAY)


def test_generation_is_opt_in_and_not_silently_called(tmp_path, monkeypatch):
    monkeypatch.setenv("ENTSOE_API_TOKEN", "TEST_TOKEN")
    calls = []
    def ee(kind, start, end):
        calls.append(kind)
        return [fixtures()[2]]
    path = tmp_path / "db"
    sync_context.sync(DAY, scope="entsoe", db=path, today=TODAY, entsoe_getter=ee)
    assert calls == ["load"]
    with pytest.raises(ValueError, match="scope both or entsoe"):
        sync_context.sync(DAY, scope="fingrid", include_generation=True,
                          db=tmp_path / "other.sqlite", today=TODAY)
