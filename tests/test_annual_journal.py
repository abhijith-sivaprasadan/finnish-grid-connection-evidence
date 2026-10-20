"""Immutable source journal contract. Synthetic rows are used only as test fixtures."""
import json
from datetime import timedelta
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
