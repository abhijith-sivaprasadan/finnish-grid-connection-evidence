"""Targeted original Fingrid gap recovery; fixtures must never be described as real."""
from datetime import datetime,timezone,timedelta
import pytest
from src.schema import OperationalRecord
from src.ingest.http import SourceError
from src.models.recover_fingrid_gaps import (
    MISSING_124_2025,NoRetryPacedClient,exact_slot,verify_original_slot,recheck
)

def fixture_row(ts:str,v=9000.0):
    start,end=exact_slot(ts)
    return OperationalRecord(source="fingrid",dataset_id="124",metric="electricity_consumption",
        unit="MWh/h",value=v,timestamp_utc=start,interval_end_utc=end,
        retrieved_at="2026-10-20T09:00:00Z",source_url="https://data.fingrid.fi/en/datasets/124")

def test_three_missing_timestamps_are_distinct_and_utc():
    assert len(MISSING_124_2025)==3
    for ts in MISSING_124_2025:
        assert exact_slot(ts)[0]==ts
        assert exact_slot(ts)[1].endswith("Z")

def test_exact_original_is_accepted_but_no_value_is_never_zero():
    for ts in MISSING_124_2025:
        got=verify_original_slot(ts,[fixture_row(ts)])
        assert got["status"]=="recovered_original_fingrid_record"
        assert got["value_mwh_per_hour"]==9000
        missing=verify_original_slot(ts,[])
        assert missing["status"]=="still_not_published"
        assert missing["value_mwh_per_hour"] is None
    with pytest.raises(ValueError,match="identity/unit/time"):
        verify_original_slot(MISSING_124_2025[0],[fixture_row(MISSING_124_2025[1])])
    with pytest.raises(ValueError,match="exactly one"):
        verify_original_slot(MISSING_124_2025[0],[fixture_row(MISSING_124_2025[0])]*2)

def test_recheck_never_claims_annual_completeness_on_three_recovered_rows():
    p=recheck(get=lambda ts,end:[fixture_row(ts)])
    assert p["recheck_status"]=="all_three_originals_recovered"
    assert len(p["interval_results"])==3
    assert p["complete_calendar_2025_source_verified"] is False
    assert p["full_year_pypsa_result_available"] is False

def test_missing_and_rate_limit_defer_without_pretending_there_are_genuine_zeros():
    p=recheck(get=lambda ts,end:[])
    assert p["recheck_status"]=="some_original_intervals_still_missing"
    assert all(r["value_mwh_per_hour"] is None for r in p["interval_results"])
    counter=[]
    def blocked(ts,end):
        counter.append(ts)
        raise SourceError("Fingrid HTTP 429, deferred")
    q=recheck(get=blocked)
    assert len(counter)==1
    assert q["recheck_status"]=="request_deferred"
    assert len(q["interval_results"])==1
    with pytest.raises(ValueError):
        NoRetryPacedClient(spacing=1.0)
