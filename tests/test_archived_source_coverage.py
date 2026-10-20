"""Offline test fixtures never claim original 2025 source observations."""
from pathlib import Path
import hashlib
import pandas as pd
import pytest
from src.models.archived_source_coverage import consolidate,validated_source,EXPECTED_SOURCES
from src.models.finland import INPUT_PATH

def stage(root:Path,name:str,frame:pd.DataFrame,role="primary"):
    p=root/name
    frame.to_csv(p,index=False)
    return {"id":name,"filename":name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
        "start":frame["timestamp_utc"].iloc[0][:10],
        "end":pd.to_datetime(frame["interval_end_utc"].iloc[-1],utc=True).date().isoformat(),
        "role":role}

def test_four_real_source_archive_fingerprints_come_from_prior_verified_artifacts():
    assert len(EXPECTED_SOURCES)==4
    assert [x["role"] for x in EXPECTED_SOURCES].count("primary")==3
    assert [x["role"] for x in EXPECTED_SOURCES].count("cross_check_only")==1
    assert len({x["sha256"] for x in EXPECTED_SOURCES})==4
    assert sum((pd.Timestamp(x["end"])-pd.Timestamp(x["start"])).days
        for x in EXPECTED_SOURCES if x["role"]=="primary")==58

def test_verified_one_day_never_becomes_verified_annual_coverage(tmp_path):
    f=pd.read_csv(INPUT_PATH).iloc[:96].copy()
    a=stage(tmp_path,"one.csv",f)
    r=consolidate(tmp_path,specs=[a],year=2026)
    assert r["verified_covered_days"]==1
    assert r["distinct_verified_paired_quarter_hours"]==96
    assert r["calendar_day_counts"]["not_covered_by_imported_archives"]==364
    assert r["complete_calendar_year_source_verified"] is False
    assert r["complete_year_pypsa_performed"] is False
    assert r["contiguous_original_source_runs"][0]["days"]==1

def test_same_original_values_with_different_retrieval_time_are_acceptable(tmp_path):
    f=pd.read_csv(INPUT_PATH).iloc[:96].copy()
    a=stage(tmp_path,"original.csv",f)
    another=f.copy()
    another["consumption_retrieved_at"]="2026-10-21T12:00:00Z"
    another["production_retrieved_at"]="2026-10-21T12:00:00Z"
    b=stage(tmp_path,"recaptured.csv",another,role="cross_check_only")
    r=consolidate(tmp_path,specs=[a,b],year=2026)
    assert r["distinct_verified_paired_quarter_hours"]==96
    another.loc[0,"consumption_mwh_per_hour"]=float(another.loc[0,"consumption_mwh_per_hour"])+1
    b=stage(tmp_path,"recaptured.csv",another,role="cross_check_only")
    with pytest.raises(ValueError,match="conflicting"):
        consolidate(tmp_path,specs=[a,b],year=2026)

def test_sha256_tampering_rejected(tmp_path):
    frame=pd.read_csv(INPUT_PATH).iloc[:96].copy()
    spec=stage(tmp_path,"source.csv",frame)
    (tmp_path/"source.csv").write_bytes((tmp_path/"source.csv").read_bytes()+b"tampered")
    with pytest.raises(ValueError,match="SHA-256"):
        validated_source(tmp_path/"source.csv",spec)
