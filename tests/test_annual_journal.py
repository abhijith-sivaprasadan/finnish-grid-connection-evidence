"""Immutable source journal contract. Synthetic rows are used only as test fixtures."""
import json
from datetime import timedelta,datetime
import pytest
from src.models.annual_journal import (
   START,END,windows,chunk_key,save_chunk,load_chunk,report,collect,complete_source_csv
)

def mk(id, start, n):
    from src.models.annual_journal import canonical
    from src.ingest.fingrid import DATASETS
    rows=[]
    for i in range(n):
        t=start+timedelta(minutes=i*15)
        b=t+timedelta(minutes=15)
        rows.append({"source":"fingrid","area":"FI","dataset_id":str(id),
            "metric":DATASETS[id][0],"unit":"MWh/h","timestamp_utc":t.isoformat().replace("+00:00","Z"),
            "interval_end_utc":b.isoformat().replace("+00:00","Z"),
            "retrieved_at":"2026-10-20T08:00:00Z","value":8000+i,"source_url":f"https://data.fingrid.fi/en/datasets/{id}"})
    return rows

def test_annual_journal_distinguishes_uncaptured_from_genuinely_missing_original(tmp_path):
    a,b=next(windows())
    p=tmp_path/(chunk_key(124,a,b)+".json")
    assert len(list(windows()))==53
    rows=mk(124,a,672)
    rows.pop(2)
    saved=save_chunk(p,124,a,b,rows)
    assert saved["source_quality"]["status"]=="original_missing"
    assert len(saved["source_quality"]["source_missing_utc"])==1
    state=report(tmp_path)
    assert state["full_calendar_2025_source_verified"] is False
    assert state["dataset_audit"]["124"]["original_missing_slots"]==1
    assert state["dataset_audit"]["74"]["uncaptured_expected_slots"]==35040
    assert state["confirmed_original_paired_slots_captured"]==0
    with pytest.raises(ValueError,match="complete"):
        complete_source_csv(tmp_path,tmp_path/"fake_annual.csv")

def test_immutable_chunks_reject_revision_or_tampering(tmp_path):
    a,b=next(windows())
    p=tmp_path/(chunk_key(124,a,b)+".json")
    records=mk(124,a,672)
    save_chunk(p,124,a,b,records)
    assert load_chunk(p,124,a,b)["source_quality"]["status"]=="complete"
    records[0]["value"]=900000
    with pytest.raises(ValueError,match="overwrite"):
        save_chunk(p,124,a,b,records)
    d=json.loads(p.read_text())
    d["original_rows"][0]["value"]=0
    p.write_text(json.dumps(d))
    with pytest.raises(ValueError,match="hash"):
        load_chunk(p,124,a,b)

def test_only_bounded_requests_and_partial_resume(tmp_path):
    from src.schema import OperationalRecord
    calls=[]
    def getter(i,a,b):
        calls.append((i,a,b))
        t=START
        if a!="2025-01-01T00:00:00Z":raise AssertionError("unexpected next chunk")
        rows=mk(i,t,672)
        return [OperationalRecord(
            source=x["source"],dataset_id=x["dataset_id"],metric=x["metric"],
            unit=x["unit"],timestamp_utc=x["timestamp_utc"],interval_end_utc=x["interval_end_utc"],
            retrieved_at=x["retrieved_at"],value=x["value"],source_url=x["source_url"])
            for x in rows]
    r=collect(tmp_path,execute=True,max_chunks=1,getter=getter)
    assert len(calls)==1
    assert r["new_original_source_chunks_saved_this_run"]==1
    assert r["full_calendar_2025_source_verified"] is False
    q=collect(tmp_path,execute=False,max_chunks=0)
    assert q["dataset_audit"]["124"]["chunks_persisted"]==1


def test_paired_day_statuses_remain_distinct_under_partial_captures(tmp_path):
    from src.models.annual_journal import daily_coverage
    a,b=next(windows())
    # First 7 days: source 124 has one true original gap; 74 is complete.
    for source in (124,74):
        rows=mk(source,a,672)
        if source==124:
            rows.pop(2)
        save_chunk(tmp_path/(chunk_key(source,a,b)+".json"),source,a,b,rows)
    report=daily_coverage(tmp_path)
    counts=report["paired_day_counts"]
    assert counts["known_source_gap"]==1
    assert counts["paired_complete"]==6
    assert counts["unknown_not_downloaded"]==358
    assert counts["all_calendar_days"]==365
    assert report["all_2025_days_verified"] is False
    assert report["missing_not_zero"] is True
    assert report["unknown_not_infeasible"] is True
    incomplete=report["daily_status"][0]
    assert incomplete["date_utc"]=="2025-01-01"
    assert incomplete["paired_status"]=="known_source_gap"
    assert incomplete["consumption_124"]["observed_original_intervals"]==95
    assert incomplete["production_74"]["observed_original_intervals"]==96
    assert incomplete["consumption_124"]["missing_source_utc"]==["2025-01-01T00:30:00.000000Z"]
    assert report["complete_contiguous_source_day_runs"][0]["consecutive_complete_days"]==6


def test_collector_prioritizes_paired_source_windows_not_entire_124_year(tmp_path):
    from src.models.annual_journal import daily_coverage
    from src.schema import OperationalRecord
    calls=[]
    a,b=next(windows())
    def getter(source_id,start,end):
        calls.append((source_id,start,end))
        low=datetime.fromisoformat(start.replace("Z","+00:00"))
        rows=mk(source_id,low,672)
        return [OperationalRecord(
          source=r["source"], dataset_id=r["dataset_id"],
          metric=r["metric"], unit=r["unit"],
          value=r["value"],timestamp_utc=r["timestamp_utc"],
          interval_end_utc=r["interval_end_utc"],retrieved_at=r["retrieved_at"],
          source_url=r["source_url"]) for r in rows]
    result=collect(tmp_path,execute=True,max_chunks=2,getter=getter)
    assert [x[0] for x in calls]==[124,74]
    assert calls[0][1]==calls[1][1]
    assert result["confirmed_original_paired_slots_captured"]==672
    assert result["paired_calendar_day_counts"]["paired_complete"]==7
    assert result["paired_calendar_day_counts"]["unknown_not_downloaded"]==358
    assert (tmp_path/"annual_2025_day_coverage.json").exists()


def test_legacy_dataset_major_journals_resume_without_redownloading(tmp_path):
    from src.schema import OperationalRecord
    a,b=next(windows())
    save_chunk(tmp_path/(chunk_key(124,a,b)+".json"),124,a,b,mk(124,a,672))
    calls=[]
    def getter(i,start,end):
        calls.append((i,start,end))
        assert i==74
        low=datetime.fromisoformat(start.replace("Z","+00:00"))
        return [OperationalRecord(
            source=r["source"],dataset_id=r["dataset_id"],
            metric=r["metric"],unit=r["unit"],value=r["value"],
            timestamp_utc=r["timestamp_utc"],interval_end_utc=r["interval_end_utc"],
            retrieved_at=r["retrieved_at"],source_url=r["source_url"])
            for r in mk(i,low,672)]
    result=collect(tmp_path,execute=True,max_chunks=1,getter=getter)
    assert len(calls)==1 and calls[0][0]==74
    assert result["confirmed_original_paired_slots_captured"]==672
