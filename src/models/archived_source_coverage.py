"""Verify and reuse existing source-attributed Fingrid 2025 archives without API calls.

The 30-day autumn archive plus winter/summer 14-day archives provide 58
DISTINCT source-complete historical UTC days, not a continuous 365-day model.
Overlapping autumn archive revisions are reported, never silently blended.
"""
from __future__ import annotations
import argparse
import csv
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from src.models.finland import load_observed
from src.models.history import canonical

EXPECTED_SOURCES=[
    {"id":"autumn30","filename":"finland_observed_15min.csv",
     "sha256":"3093f704484848919d83feb6c133c2e2abf2299566d5bd02a109e01b7fdec2e0",
     "start":"2025-09-15","end":"2025-10-15","role":"primary",
     "run_id":39391985966,"artifact_id":12249992474},
    {"id":"winter14","filename":"fi_winter_matched_2025.csv",
     "sha256":"b0504230744d16020e253dd48bbeb7693459414ab0893f3770f6adc188596977",
     "start":"2025-01-18","end":"2025-02-01","role":"primary",
     "run_id":39396079522,"artifact_id":12251493864},
    {"id":"summer14","filename":"fi_summer_matched_2025.csv",
     "sha256":"d8ad5dc81ecee9b7b410aa19c2316faff16d55827a48d5fd59bcb667bf16a679",
     "start":"2025-06-15","end":"2025-06-29","role":"primary",
     "run_id":39396079522,"artifact_id":12251493864},
    {"id":"autumn14","filename":"fi_autumn_matched_2025.csv",
     "sha256":"a38d703c23037bae75370e6414ff4b0034eb64b9832ea15167e40141c44235be",
     "start":"2025-09-15","end":"2025-09-29","role":"cross_check_only",
     "run_id":39396079522,"artifact_id":12251493864}
]
SOURCE_COLUMNS=("timestamp_utc","interval_end_utc","consumption_mwh_per_hour",
                "production_mwh_per_hour","consumption_retrieved_at","production_retrieved_at")
ORIGINAL_GAPS=("2025-01-17T17:00:00Z","2025-01-17T17:45:00Z",
               "2025-07-11T16:15:00Z")
RECOVERY_RUN="https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39406458886"


def validated_source(path:Path, spec:dict)->list[dict]:
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest!=spec["sha256"]:
        raise ValueError(f"Source archive {spec['id']} SHA-256 differs; original record rejected")
    verified=load_observed(path)
    start=spec["start"]+"T00:00:00.000000Z"
    end=spec["end"]+"T00:00:00.000000Z"
    if (len(verified)!=(date.fromisoformat(spec["end"])-date.fromisoformat(spec["start"])).days*96
        or canonical(verified["timestamp_utc"].iloc[0])!=canonical(start)
        or canonical(verified["interval_end_utc"].iloc[-1])!=canonical(end)):
        raise ValueError(f"Source archive {spec['id']} does not cover its independently verified date window")
    rows=[]
    with path.open(encoding="utf-8",newline="") as f:
        reader=csv.DictReader(f)
        if set(reader.fieldnames or ())!=set(SOURCE_COLUMNS):
            raise ValueError("Unexpected original Fingrid source CSV schema")
        for row in reader:
            rows.append({
                "start_utc":canonical(row["timestamp_utc"]),
                "end_utc":canonical(row["interval_end_utc"]),
                "consumption_mwh_per_hour":Decimal(row["consumption_mwh_per_hour"]),
                "production_mwh_per_hour":Decimal(row["production_mwh_per_hour"]),
                "consumption_retrieved_at":canonical(row["consumption_retrieved_at"]),
                "production_retrieved_at":canonical(row["production_retrieved_at"]),
                "archive_id":spec["id"]
            })
    if len(rows)!=len(verified):
        raise ValueError("Operator CSV row count changed during verification")
    return rows


def consolidate(location:Path,*,specs:list[dict]|None=None,year:int=2025)->dict:
    specs=EXPECTED_SOURCES if specs is None else specs
    observed={}
    conflicts=[]
    archived=[]
    for spec in specs:
        path=location/spec["filename"]
        rows=validated_source(path,spec)
        archived.append({k:spec[k] for k in ("id","sha256","start","end","role","run_id","artifact_id") if k in spec})
        for row in rows:
            key=row["start_utc"]
            previous=observed.get(key)
            if previous is None:
                if spec["role"]!="primary":
                    raise ValueError("Cross-check-only archive is outside all primary source windows")
                observed[key]=row
                continue
            if (previous["consumption_mwh_per_hour"]!=row["consumption_mwh_per_hour"]
                or previous["production_mwh_per_hour"]!=row["production_mwh_per_hour"]):
                conflicts.append({"timestamp_utc":key,"original_capture":previous["archive_id"],
                                  "later_capture":row["archive_id"],
                                  "status":"source_revision_disagreement_requires_review"})
    if conflicts:
        raise ValueError(f"{len(conflicts)} conflicting historical Fingrid 124/74 readings across separately verified archives; refusing combined source summary")
    days={}
    cursor=date(year,1,1)
    last=date(year+1,1,1)
    gaps={date.fromisoformat(ts[:10]) for ts in ORIGINAL_GAPS} if year==2025 else set()
    while cursor<last:
        day=cursor.isoformat()
        # The completeness calculation uses exact UTC timestamps, not rounded dates.
        midnight=datetime(cursor.year,cursor.month,cursor.day,tzinfo=timezone.utc)
        count=sum((midnight+timedelta(minutes=15*i)).strftime("%Y-%m-%dT%H:%M:%S.%fZ") in observed for i in range(96))
        status=("paired_original_archived_complete" if count==96 else
                "partial_archived_day_not_model_eligible" if count>0 else
                "known_missing_in_separate_operator_recheck" if cursor in gaps else
                "not_covered_by_imported_archives")
        days[day]={"status":status,"archived_paired_slots":count,"expected_paired_slots":96}
        cursor+=timedelta(days=1)
    grouped={}
    for state in ("paired_original_archived_complete","partial_archived_day_not_model_eligible",
                  "known_missing_in_separate_operator_recheck","not_covered_by_imported_archives"):
        grouped[state]=sum(x["status"]==state for x in days.values())
    if sum(grouped.values())!=(last-date(year,1,1)).days:
        raise AssertionError("Calendar day coverage audit does not partition the year")
    if len(observed)!=sum(x["archived_paired_slots"] for x in days.values()):
        raise AssertionError("Archive-backed time series contains duplicated or unaccounted timestamps")
    runs=[]
    current=None
    for day,record in days.items():
        if record["status"]=="paired_original_archived_complete":
            if current is None:current=day
        elif current:
            runs.append({"start_utc":current+"T00:00:00Z",
                         "end_exclusive_utc":day+"T00:00:00Z",
                         "days":(date.fromisoformat(day)-date.fromisoformat(current)).days})
            current=None
    if current:
        runs.append({"start_utc":current+"T00:00:00Z","end_exclusive_utc":str(last)+"T00:00:00Z",
                     "days":(last-date.fromisoformat(current)).days})
    consumed=sum((r["consumption_mwh_per_hour"]*Decimal("0.25") for r in observed.values()),Decimal(0))
    produced=sum((r["production_mwh_per_hour"]*Decimal("0.25") for r in observed.values()),Decimal(0))
    return {
      "status":"verified_archive_coverage_only",
      "kind":"historical_original_operator_source_observations",
      "year":year,
      "source_datasets":[124,74],
      "source_urls":["https://data.fingrid.fi/en/datasets/124","https://data.fingrid.fi/en/datasets/74"],
      "source_archive_records":archived,
      "distinct_verified_paired_quarter_hours":len(observed),
      "verified_covered_days":grouped["paired_original_archived_complete"],
      "calendar_day_counts":grouped,
      "contiguous_original_source_runs":runs,
      "verified_sample_consumption_gwh":str(round(consumed/Decimal(1000),3)),
      "verified_sample_production_gwh":str(round(produced/Decimal(1000),3)),
      "sample_energy_scope":"Only archived, independently verified periods; NOT a full-year electricity consumption/production total",
      "external_original_gaps_utc":list(ORIGINAL_GAPS) if year==2025 else [],
      "external_missing_evidence_run":RECOVERY_RUN if year==2025 else None,
      "unarchived_days_remain_unknown":True,
      "complete_calendar_year_source_verified":False,
      "complete_year_pypsa_performed":False,
      "site_connectability_confirmed":False,
      "per_day":days,
      "limitations":[
        "Verified selected archives are not a complete annual record and cannot be annualized as observed national electricity totals.",
        "Three original dataset-124 source gaps were separately rechecked but cannot be assigned zero or inferred from adjacent periods.",
        "Overlapping historical archive observations must agree on native numerical source values; any revision conflict rejects this entire combined summary.",
        "Original retrieval timestamps may legitimately differ between otherwise identical source captures; both original artifact SHA-256 values remain cited.",
        "This is only a national historical observations coverage bank, not a source for grid station headroom, 2030 projections or transmission line constraints.",
        "Do not concatenate disjoint historical days as one PyPSA battery/storage simulation: model each uninterrupted original-source run independently."
      ]
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--autumn-30",type=Path,required=True)
    p.add_argument("--seasons-14",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args(argv)
    paths=args.output.parent/"verified_archives"
    paths.mkdir(parents=True,exist_ok=True)
    import shutil
    for name,src in [
      ("finland_observed_15min.csv",args.autumn_30/"finland_observed_15min.csv"),
      ("fi_winter_matched_2025.csv",args.seasons_14/"fi_winter_matched_2025.csv"),
      ("fi_summer_matched_2025.csv",args.seasons_14/"fi_summer_matched_2025.csv"),
      ("fi_autumn_matched_2025.csv",args.seasons_14/"fi_autumn_matched_2025.csv"),
    ]:
        shutil.copyfile(src,paths/name)
    report=consolidate(paths)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("ARCHIVED_2025_COVERAGE_JSON="+json.dumps({
      "paired_source_intervals":report["distinct_verified_paired_quarter_hours"],
      "covered_source_days":report["verified_covered_days"],
      "day_status_counts":report["calendar_day_counts"],
      "verified_source_runs":report["contiguous_original_source_runs"],
      "annual_complete":report["complete_calendar_year_source_verified"]
    },sort_keys=True))


if __name__=="__main__":
    main()
