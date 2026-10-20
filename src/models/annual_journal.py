"""Resumable, immutable original-source Fingrid 2025 audit. No fill and no implied full-year coverage.

Manual max-chunk batches allow slow source access without re-fetching completed
windows. Cached rows carry source IDs, timestamp/units, retrieval time and hash.
A successful fetch with *missing source rows* is NOT a transport failure;
"not_downloaded", "original_missing", and "complete" are distinct statuses.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime,date,time,timedelta,timezone
import hashlib
import json
import math
import os
from pathlib import Path

from src.ingest.fingrid import DATASETS,fetch
from src.ingest.http import SourceError
from src.models.history import canonical,write_pair
from src.models.recover_fingrid_gaps import NoRetryPacedClient

START=datetime(2025,1,1,tzinfo=timezone.utc)
END=datetime(2026,1,1,tzinfo=timezone.utc)
DATASET_IDS=(124,74)
EXPECTED_PAIRS=35040
CHUNK_DAYS=7


def windows():
    cursor=START
    while cursor<END:
        nxt=min(cursor+timedelta(days=CHUNK_DAYS),END)
        yield cursor,nxt
        cursor=nxt


def chunk_key(dataset_id:int,start:datetime,end:datetime)->str:
    return f"fingrid_{dataset_id}_{start:%Y%m%d}_{end:%Y%m%d}"


def check_source_record(row:dict,dataset_id:int,start:datetime,end:datetime):
    metric,unit=DATASETS[dataset_id]
    if (row.get("source")!="fingrid" or row.get("area")!="FI" or
        row.get("dataset_id")!=str(dataset_id) or row.get("metric")!=metric or
        row.get("unit")!=unit or row.get("source_url")!=f"https://data.fingrid.fi/en/datasets/{dataset_id}"):
        raise ValueError("Cached source row has wrong dataset identity or native unit")
    ts=datetime.fromisoformat(canonical(row["timestamp_utc"]).replace("Z","+00:00"))
    finish=datetime.fromisoformat(canonical(row["interval_end_utc"]).replace("Z","+00:00"))
    if not start<=ts<finish<=end or finish-ts!=timedelta(minutes=15):
        raise ValueError("Cached source timestamp is outside original queried time window")
    if ts.minute%15 or ts.second or ts.microsecond:
        raise ValueError("Non-quarter-hour original source timestamp")
    v=float(row["value"])
    if not math.isfinite(v) or v<0:
        raise ValueError("Missing or nonphysical operator value")
    canonical(row["retrieved_at"])
    return ts


def source_row(record)->dict:
    return {
      "source":record.source,"area":record.area,
      "dataset_id":record.dataset_id,"metric":record.metric,"unit":record.unit,
      "timestamp_utc":canonical(record.timestamp_utc),
      "interval_end_utc":canonical(record.interval_end_utc),
      "retrieved_at":canonical(record.retrieved_at),
      "value":float(record.value),
      "source_url":record.source_url,
    }


def digest_rows(rows)->str:
    return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def quarantine_kind(row:dict,dataset_id:int,start:datetime,end:datetime)->str:
    """Verify an authentic but incompatible native interval without regridding it.

    Only two specifically established cases are retained: a source 15-minute
    interval with an off-quarter-hour start, and a native 30-minute interval.
    Unexpected durations, metadata or values must still fail closed.
    """
    metric,unit=DATASETS[dataset_id]
    if (row.get("source")!="fingrid" or row.get("area")!="FI" or
        row.get("dataset_id")!=str(dataset_id) or row.get("metric")!=metric or
        row.get("unit")!=unit or row.get("source_url")!=f"https://data.fingrid.fi/en/datasets/{dataset_id}"):
        raise ValueError("Cached source row has wrong dataset identity or native unit")
    ts=datetime.fromisoformat(canonical(row["timestamp_utc"]).replace("Z","+00:00"))
    finish=datetime.fromisoformat(canonical(row["interval_end_utc"]).replace("Z","+00:00"))
    if not start<=ts<finish<=end:
        raise ValueError("Cached source timestamp is outside original queried time window")
    value=float(row["value"])
    if not math.isfinite(value) or value<0:
        raise ValueError("Invalid quarantined source value")
    canonical(row["retrieved_at"])
    duration=finish-ts
    aligned=(ts.minute%15==0 and ts.second==0 and ts.microsecond==0)
    if duration==timedelta(minutes=15) and not aligned:
        return "off_grid_original_15min"
    if duration==timedelta(minutes=30) and aligned:
        return "native_30min_interval"
    raise ValueError("Unsupported native source interval; do not regrid or silently quarantine")


def split_aligned_and_quarantined(rows:list[dict],dataset_id:int,start:datetime,end:datetime):
    """Keep both ordinary aligned records and verified irregular originals.

    Irregular originals are excluded from all quarter-hour matching, daily
    completeness and optimization. Their exact operator starts/ends survive.
    """
    aligned,quarantined=[],[]
    for row in rows:
        try:
            check_source_record(row,dataset_id,start,end)
        except ValueError:
            quarantine_kind(row,dataset_id,start,end)
            quarantined.append(row)
        else:
            aligned.append(row)
    return aligned,quarantined


def validate_quarantined(rows:list[dict],dataset_id:int,start:datetime,end:datetime):
    for row in rows:
        quarantine_kind(row,dataset_id,start,end)


def quarantine_status(rows:list[dict],dataset_id:int,start:datetime,end:datetime)->str:
    kinds={quarantine_kind(row,dataset_id,start,end) for row in rows}
    if "native_30min_interval" in kinds:
        return "operator_native_30min_interval_preserved_not_interpolated"
    return "operator_off_grid_timestamp_not_regular_15min_slot"


def chunk_audit(rows:list[dict],dataset_id:int,start:datetime,end:datetime):
    found={}
    for row in rows:
        ts=check_source_record(row,dataset_id,start,end)
        if ts in found:
            raise ValueError("Duplicate original source timestamp; never select favorable reading")
        found[ts]=row
    target=int((end-start).total_seconds()/900)
    missing=[(start+timedelta(minutes=15*i)).strftime("%Y-%m-%dT%H:%M:%SZ")
             for i in range(target)
             if (start+timedelta(minutes=15*i)) not in found]
    return {"expected_slots":target,"observed_original_slots":len(found),"source_missing_utc":missing,
            "status":"complete" if not missing else "original_missing"}


def save_chunk(path:Path,dataset_id:int,start:datetime,end:datetime,rows:list[dict],*,off_grid_rows=None):
    values=sorted(rows,key=lambda r:r["timestamp_utc"])
    analysis=chunk_audit(values,dataset_id,start,end)
    payload={"kind":"Fingrid_source_capture_not_model","dataset_id":dataset_id,
             "source_window_start_utc":start.isoformat().replace("+00:00","Z"),
             "source_window_end_utc":end.isoformat().replace("+00:00","Z"),
             "original_rows":values,"original_rows_sha256":digest_rows(values),
             "source_quality":analysis}
    if off_grid_rows:
        quarantine=sorted(off_grid_rows,key=lambda r:r["timestamp_utc"])
        validate_quarantined(quarantine,dataset_id,start,end)
        payload["off_grid_original_source_rows"]=quarantine
        payload["off_grid_original_source_rows_sha256"]=digest_rows(quarantine)
        payload["quarantine_status"]=quarantine_status(quarantine,dataset_id,start,end)
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(".tmp")
    if path.exists():
        old=load_chunk(path,dataset_id,start,end)
        if old["original_rows_sha256"]!=payload["original_rows_sha256"]:
            raise ValueError("Refusing to overwrite different historical source revision")
        return old
    temp.write_text(json.dumps(payload,separators=(",",":"))+"\n",encoding="utf-8")
    os.replace(temp,path)
    return payload


def load_chunk(path:Path,dataset_id:int,start:datetime,end:datetime):
    payload=json.loads(path.read_text(encoding="utf-8"))
    if (payload.get("dataset_id")!=dataset_id or
        payload.get("source_window_start_utc")!=start.isoformat().replace("+00:00","Z") or
        payload.get("source_window_end_utc")!=end.isoformat().replace("+00:00","Z") or
        payload.get("kind")!="Fingrid_source_capture_not_model"):
        raise ValueError("Cached source window identity mismatch")
    values=payload["original_rows"]
    if digest_rows(values)!=payload["original_rows_sha256"] or (
        chunk_audit(values,dataset_id,start,end)!=payload["source_quality"]):
        raise ValueError("Cached source window hash or completeness metadata inconsistent")
    quarantined=payload.get("off_grid_original_source_rows",[])
    if quarantined:
        if (digest_rows(quarantined)!=payload.get("off_grid_original_source_rows_sha256") or
            payload.get("quarantine_status")!=quarantine_status(quarantined,dataset_id,start,end)):
            raise ValueError("Cached source quarantine hash or original identity inconsistent")
        validate_quarantined(quarantined,dataset_id,start,end)
    elif "off_grid_original_source_rows_sha256" in payload:
        raise ValueError("Unexpected off-grid original source digest without original data")
    return payload


def report(directory:Path)->dict:
    fetched={}
    combined={124:{},74:{}}
    all_windows=list(windows())
    problems=[]
    for dataset_id in DATASET_IDS:
        counts={"chunks_persisted":0,"original_missing_slots":0,"uncaptured_expected_slots":0,"quarantined_operator_source_intervals":0}
        for a,b in all_windows:
            path=directory/(chunk_key(dataset_id,a,b)+".json")
            expected=int((b-a).total_seconds()/900)
            if not path.exists():
                counts["uncaptured_expected_slots"]+=expected
                continue
            payload=load_chunk(path,dataset_id,a,b)
            counts["chunks_persisted"]+=1
            counts["original_missing_slots"]+=len(payload["source_quality"]["source_missing_utc"])
            counts["quarantined_operator_source_intervals"]+=len(payload.get("off_grid_original_source_rows",[]))
            for row in payload.get("off_grid_original_source_rows",[]):
                problems.append({"dataset_id":dataset_id,
                  "timestamp_utc":row["timestamp_utc"],
                  "interval_end_utc":row["interval_end_utc"],
                  "status":"authentic_source_"+quarantine_kind(row,dataset_id,a,b)+"_quarantined_not_interpolated"})
            for ts in payload["source_quality"]["source_missing_utc"]:
                problems.append({"dataset_id":dataset_id,"timestamp_utc":ts,"status":"original_missing_at_capture"})
            for r in payload["original_rows"]:
                key=canonical(r["timestamp_utc"])
                if key in combined[dataset_id]:
                    raise ValueError("Duplicate across capture journal chunks")
                combined[dataset_id][key]=r
        fetched[str(dataset_id)]=counts
    keys=set(combined[124])&set(combined[74])
    complete=(all(fetched[str(i)]["chunks_persisted"]==len(all_windows) for i in DATASET_IDS)
              and all(fetched[str(i)]["original_missing_slots"]==0 for i in DATASET_IDS)
              and len(keys)==EXPECTED_PAIRS)
    return {
      "historical_year":2025,"kind":"original_source_capture_inventory",
      "full_calendar_2025_source_verified":complete,
      "expected_original_pairs":EXPECTED_PAIRS,
      "confirmed_original_paired_slots_captured":len(keys),
      "scheduled_chunks_per_dataset":len(all_windows),
      "dataset_audit":fetched,
      "original_missing_intervals_in_captured_windows":problems,
      "unfetched_chunks_are_unknown_not_zero":True,
      "unknown_is_not_source_absent":True,
      "annual_energy_total_verified":complete,
      "network_capacity_confirmed":False,
      "source_urls":["https://data.fingrid.fi/en/datasets/124","https://data.fingrid.fi/en/datasets/74"],
    }


def daily_coverage(directory:Path)->dict:
    """Explicit observed/unknown/missing/paired source status for every UTC day.

    No amount of stored data can transform a missing interval into a 0 MW value.
    Only source-complete days in *both* datasets are eligible for PyPSA windows.
    """
    source_by_day={}
    for dataset_id in DATASET_IDS:
        cursor=START
        while cursor<END:
            key=cursor.date().isoformat()
            source_by_day.setdefault(key,{})
            cursor+=timedelta(days=1)
        for start,stop in windows():
            path=directory/(chunk_key(dataset_id,start,stop)+".json")
            if not path.exists():
                cursor=start
                while cursor<stop:
                    source_by_day[cursor.date().isoformat()][str(dataset_id)]={
                        "status":"not_downloaded","observed_original_intervals":None,
                        "expected_intervals":96,"missing_source_utc":None}
                    cursor+=timedelta(days=1)
                continue
            chunk=load_chunk(path,dataset_id,start,stop)
            by_date={}
            for row in chunk["original_rows"]:
                day=row["timestamp_utc"][:10]
                by_date.setdefault(day,[]).append(canonical(row["timestamp_utc"]))
            cursor=start
            while cursor<stop:
                day=cursor.date().isoformat()
                actual=by_date.get(day,[])
                observed=set(actual)
                expected=[(cursor+timedelta(minutes=15*i)).strftime("%Y-%m-%dT%H:%M:%S.%fZ") for i in range(96)]
                missing=[ts for ts in expected if ts not in observed]
                source_by_day[day][str(dataset_id)]={
                    "status":"source_complete" if not missing else "original_missing_at_capture",
                    "observed_original_intervals":len(actual),
                    "expected_intervals":96,
                    "missing_source_utc":missing
                }
                cursor+=timedelta(days=1)
    results=[]
    runs=[]
    first=None
    for day,ids in sorted(source_by_day.items()):
        consumption=ids["124"]
        production=ids["74"]
        if "not_downloaded" in (consumption["status"],production["status"]):
            state="unknown_not_downloaded"
        elif "original_missing_at_capture" in (consumption["status"],production["status"]):
            state="known_source_gap"
        else:
            state="paired_complete"
        if state=="paired_complete":
            if first is None: first=day
        elif first is not None:
            end=date.fromisoformat(day)
            runs.append({"start_utc":first+"T00:00:00Z","end_utc_exclusive":end.isoformat()+"T00:00:00Z",
                         "consecutive_complete_days":(end-date.fromisoformat(first)).days})
            first=None
        results.append({"date_utc":day,"paired_status":state,
                        "consumption_124":consumption,"production_74":production})
    if first is not None:
        runs.append({"start_utc":first+"T00:00:00Z","end_utc_exclusive":"2026-01-01T00:00:00Z",
                     "consecutive_complete_days":(END.date()-date.fromisoformat(first)).days})
    counts={state:sum(1 for x in results if x["paired_status"]==state)
            for state in ("paired_complete","known_source_gap","unknown_not_downloaded")}
    counts["all_calendar_days"]=len(results)
    if len(results)!=365 or sum(counts[x] for x in ("paired_complete","known_source_gap","unknown_not_downloaded"))!=365:
        raise AssertionError("Annual daily coverage partition is inconsistent")
    return {"source_period":"2025 calendar UTC",
            "data_kind":"observed_source_completeness_only",
            "paired_day_counts":counts,
            "complete_contiguous_source_day_runs":sorted(runs,key=lambda r:(-r["consecutive_complete_days"],r["start_utc"])),
            "daily_status":results,
            "all_2025_days_verified":counts["paired_complete"]==365,
            "missing_not_zero":True,
            "unknown_not_infeasible":True}


def collect(directory:Path, *,execute=False,max_chunks=8,getter=None,client=None)->dict:
    if not 0<=max_chunks<=16:
        raise ValueError("Limit each manual annual download run to at most 16 source chunks")
    if execute and getter is None and not os.environ.get("FINGRID_API_KEY"):
        raise SourceError("Private Fingrid API key required for explicit annual source requests")
    client=client or NoRetryPacedClient(spacing=5.0)
    num=0
    deferred=False
    # Collect by *time window*, not by whole dataset. This permits early paired
    # source coverage verification without waiting for all 124 chunks before 74.
    # Journals written by the previous dataset-major collector still resume.
    for a,b in windows():
        for dataset_id in DATASET_IDS:
            path=directory/(chunk_key(dataset_id,a,b)+".json")
            if path.exists():
                load_chunk(path,dataset_id,a,b)
                continue
            if not execute or num>=max_chunks or deferred:
                continue
            x=a.isoformat().replace("+00:00","Z")
            y=b.isoformat().replace("+00:00","Z")
            try:
                observations=(getter(dataset_id,x,y) if getter is not None else fetch(dataset_id,x,y,client=client))
            except SourceError:
                deferred=True
                break
            values=[source_row(r) for r in observations]
            aligned,quarantined=split_aligned_and_quarantined(values,dataset_id,a,b)
            save_chunk(path,dataset_id,a,b,aligned,off_grid_rows=quarantined)
            num+=1
        if deferred:break
    state=report(directory)
    coverage=daily_coverage(directory)
    state["paired_calendar_day_counts"]=coverage["paired_day_counts"]
    state["complete_contiguous_source_day_runs"]=coverage["complete_contiguous_source_day_runs"]
    # This separate compact-source-status artifact never claims a full year of
    # 15-minute observations if any day was not downloaded or was source-missing.
    directory.mkdir(parents=True,exist_ok=True)
    (directory/"annual_2025_day_coverage.json").write_text(json.dumps(coverage,indent=2)+"\n",encoding="utf-8")
    state["new_original_source_chunks_saved_this_run"]=num
    state["rate_limit_or_access_deferred"]=deferred
    state["collection_status"]=("full_year_source_verified" if state["full_calendar_2025_source_verified"]
        else "deferred_due_to_rate_limit_or_source_error" if deferred
        else "partial_source_inventory")
    directory.mkdir(parents=True,exist_ok=True)
    (directory/"annual_2025_journal_audit.json").write_text(json.dumps(state,indent=2)+"\n",encoding="utf-8")
    return state


def complete_source_csv(directory:Path,target:Path)->dict:
    """Refuse a year CSV unless both native operator feeds fully validate."""
    manifest=report(directory)
    if not manifest["full_calendar_2025_source_verified"]:
        raise ValueError("2025 operator record not complete; full-year dataset must not be asserted")
    combined={}
    for dataset_id in DATASET_IDS:
        record={}
        for a,b in windows():
            path=directory/(chunk_key(dataset_id,a,b)+".json")
            for item in load_chunk(path,dataset_id,a,b)["original_rows"]:
                record[canonical(item["timestamp_utc"])]=item
        combined[dataset_id]=record
    paired=[]
    for i in range(EXPECTED_PAIRS):
        dt=START+timedelta(minutes=15*i)
        ts=dt.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
        end=(dt+timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S.000000Z")
        one,two=combined[124][ts],combined[74][ts]
        paired.append({
          "timestamp_utc":ts,"interval_end_utc":end,
          "consumption_mwh_per_hour":str(one["value"]),
          "production_mwh_per_hour":str(two["value"]),
          "consumption_retrieved_at":one["retrieved_at"],
          "production_retrieved_at":two["retrieved_at"]
        })
    result=write_pair(paired,target,window_start="2025-01-01",window_end="2026-01-01")
    result["complete_calendar_2025_source_verified"]=True
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dir",type=Path,required=True)
    p.add_argument("--execute",action="store_true")
    p.add_argument("--max-new-chunks",type=int,default=8)
    args=p.parse_args(argv)
    status=collect(args.dir,execute=args.execute,max_chunks=args.max_new_chunks)
    if status["full_calendar_2025_source_verified"]:
        extra=complete_source_csv(args.dir,args.dir.parent/"fingrid_2025_source_complete.csv")
        status["full_source_csv_manifest"]=extra
        (args.dir/"annual_2025_journal_audit.json").write_text(json.dumps(status,indent=2)+"\n")
    print("FINGRID_RESUMABLE_ANNUAL_JSON="+json.dumps({
       k:status[k] for k in ("collection_status","full_calendar_2025_source_verified",
         "confirmed_original_paired_slots_captured","scheduled_chunks_per_dataset",
         "new_original_source_chunks_saved_this_run","rate_limit_or_access_deferred")
    },sort_keys=True))


if __name__=="__main__":
    main()
