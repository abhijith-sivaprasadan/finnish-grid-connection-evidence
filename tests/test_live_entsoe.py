"""Offline tests only: no credentials or network traffic."""
from datetime import date
import json
import pytest
from src import live_entsoe
from src.ingest.http import SourceError
from src.schema import OperationalRecord


def record():
    return OperationalRecord(
        source="entsoe", dataset_id="A65", metric="electricity_consumption",
        unit="MW", value=125.0, timestamp_utc="2026-10-13T00:00:00+00:00",
        interval_end_utc="2026-10-13T00:15:00+00:00",
        retrieved_at="2026-10-17T00:00:00+00:00",
        source_url="https://transparency.entsoe.eu/",
    )


def test_default_day_is_three_days_before_today():
    assert live_entsoe.completed_utc_day(today=date(2026, 10, 17)) == (
        "2026-10-14T00:00:00Z", "2026-10-15T00:00:00Z")


@pytest.mark.parametrize("value", ["2026-10-16", "2026-10-17", "2026-10-18", "yesterday", "2026-1-2"])
def test_invalid_or_incomplete_day_fails(value):
    with pytest.raises(ValueError):
        live_entsoe.completed_utc_day(value, today=date(2026, 10, 17))


def test_authenticated_response_is_temporary_and_credentials_not_printed(monkeypatch, capsys):
    marker = "FAKE_TEST_TOKEN_DO_NOT_PUBLISH"
    monkeypatch.setenv("ENTSOE_API_TOKEN", marker)
    observed = []
    def fake_fetch(kind, start, end):
        observed.append((kind, start, end))
        return [record()]
    result = live_entsoe.live_smoke(day="2026-10-13", kind="load",
        getter=fake_fetch, today=date(2026, 10, 17))
    print(json.dumps(result))
    assert result["records"] == 1 and result["inserted"] == 1
    assert result["metrics"] == ["electricity_consumption"]
    assert result["persistence"] == "temporary database deleted after check"
    assert marker not in capsys.readouterr().out
    assert observed == [("load", "2026-10-13T00:00:00Z", "2026-10-14T00:00:00Z")]


def test_does_not_call_source_without_secret(monkeypatch):
    monkeypatch.delenv("ENTSOE_API_TOKEN", raising=False)
    def should_not_run(*args):
        raise AssertionError("No fetch allowed without a secret")
    with pytest.raises(SourceError, match="ENTSOE_API_TOKEN"):
        live_entsoe.live_smoke(day="2026-10-13", getter=should_not_run,
                              today=date(2026, 10, 17))


def test_zero_response_fails_without_marking_ready(monkeypatch):
    monkeypatch.setenv("ENTSOE_API_TOKEN", "TEST_ONLY")
    with pytest.raises(SourceError, match="No time-series"):
        live_entsoe.live_smoke(day="2026-10-13", getter=lambda *args: [],
                              today=date(2026, 10, 17))
