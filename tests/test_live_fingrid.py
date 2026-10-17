"""Synthetic/offline tests: never contact Fingrid or use real API keys."""
from datetime import date
import json
import pytest

from src import live_fingrid
from src.ingest.http import SourceError
from src.schema import OperationalRecord

TODAY = date(2026, 10, 17)


def record(dataset_id=124, *, metric=None, source="fingrid", timestamp=None):
    return OperationalRecord(
        source=source,
        dataset_id=str(dataset_id),
        metric=metric or ("electricity_consumption" if dataset_id == 124 else "electricity_production"),
        unit="MWh/h",
        value=7300.0 if dataset_id == 124 else 6000.0,
        timestamp_utc=timestamp or "2026-10-13T00:00:00Z",
        interval_end_utc="2026-10-13T00:15:00Z",
        retrieved_at="2026-10-17T00:00:00Z",
        source_url=f"https://data.fingrid.fi/en/datasets/{dataset_id}",
    )


def test_both_datasets_are_preserved_as_national_context(monkeypatch, capsys):
    secret_marker = "DUMMY_TEST_KEY_NOT_REAL"
    monkeypatch.setenv("FINGRID_API_KEY", secret_marker)
    calls = []

    def fake_getter(dataset_id, start, end):
        calls.append((dataset_id, start, end))
        return [record(dataset_id)]

    result = live_fingrid.live_smoke(
        day="2026-10-13", getter=fake_getter, today=TODAY
    )
    print(json.dumps(result))
    assert result["status"] == "authenticated_source_parse_and_temporary_db_insert_passed"
    assert result["records"] == 2
    assert result["dataset_ids"] == ["124", "74"]
    assert result["records_by_dataset"] == {"124": 1, "74": 1}
    assert result["source_units"] == {"124": "MWh/h", "74": "MWh/h"}
    assert result["persistence"] == "temporary database deleted after check"
    assert secret_marker not in capsys.readouterr().out
    assert calls == [
        (124, "2026-10-13T00:00:00Z", "2026-10-14T00:00:00Z"),
        (74, "2026-10-13T00:00:00Z", "2026-10-14T00:00:00Z"),
    ]


def test_single_dataset(monkeypatch):
    monkeypatch.setenv("FINGRID_API_KEY", "TEST_ONLY")
    result = live_fingrid.live_smoke(day="2026-10-13", kind="consumption",
        getter=lambda *args: [record(124)], today=TODAY)
    assert result["records_by_dataset"] == {"124": 1}


def test_no_secret_stops_before_fetch(monkeypatch):
    monkeypatch.delenv("FINGRID_API_KEY", raising=False)
    def unexpected(*args):
        raise AssertionError("Must not fetch without secret")
    with pytest.raises(SourceError, match="FINGRID_API_KEY"):
        live_fingrid.live_smoke(day="2026-10-13",
            getter=unexpected, today=TODAY)


@pytest.mark.parametrize("kind", ["", "all", "invalid", "ENTSO-E"])
def test_unknown_kind_rejected(monkeypatch, kind):
    monkeypatch.setenv("FINGRID_API_KEY", "TEST_ONLY")
    with pytest.raises(ValueError, match="consumption, production or both"):
        live_fingrid.live_smoke(day="2026-10-13",
            kind=kind, getter=lambda *args: [record(124)], today=TODAY)


def test_empty_response_fails(monkeypatch):
    monkeypatch.setenv("FINGRID_API_KEY", "TEST_ONLY")
    with pytest.raises(SourceError, match="No Fingrid observations"):
        live_fingrid.live_smoke(day="2026-10-13", getter=lambda *args: [],
            today=TODAY)


def test_source_mixup_is_rejected(monkeypatch):
    monkeypatch.setenv("FINGRID_API_KEY", "TEST_ONLY")
    with pytest.raises(ValueError, match="Unexpected source/dataset/unit"):
        live_fingrid.live_smoke(day="2026-10-13",
            getter=lambda *args: [record(74)],
            kind="consumption", today=TODAY)


def test_duplicate_interval_is_rejected(monkeypatch):
    monkeypatch.setenv("FINGRID_API_KEY", "TEST_ONLY")
    with pytest.raises(ValueError, match="Duplicate Fingrid observation"):
        live_fingrid.live_smoke(day="2026-10-13",
            getter=lambda *args: [record(124), record(124)],
            kind="consumption", today=TODAY)


def test_out_of_window_is_rejected(monkeypatch):
    monkeypatch.setenv("FINGRID_API_KEY", "TEST_ONLY")
    with pytest.raises(ValueError, match="outside requested day"):
        live_fingrid.live_smoke(day="2026-10-13",
            getter=lambda *args: [record(124, timestamp="2026-10-12T22:00:00Z")],
            kind="consumption", today=TODAY)


def test_incomplete_day_is_rejected(monkeypatch):
    monkeypatch.setenv("FINGRID_API_KEY", "TEST_ONLY")
    with pytest.raises(ValueError, match="two days in the past"):
        live_fingrid.live_smoke(day="2026-10-16",
            getter=lambda *args: [record(124)], today=TODAY)
