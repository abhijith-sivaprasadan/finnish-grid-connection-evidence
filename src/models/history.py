"""Strict, opt-in long-history Fingrid pairing for PyPSA system sensitivities.

No fabricated intervals, no credential serialization, no writes to Neon.
Supports complete 15-minute UTC days only (newer than the 2023 resolution change).
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, time, timedelta, timezone
import hashlib
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
import os

from src.ingest.fingrid import DATASETS, fetch
from src.ingest.http import HttpClient, SourceError
from src.models.finland import load_observed

ROOT=Path(__file__).resolve().parents[2]
UTC=timezone.utc
FIELDS=["timestamp_utc","interval_end_utc","consumption_mwh_per_hour",
        "production_mwh_per_hour","consumption_retrieved_at","production_retrieved_at"]
VALID_AFTER=date(2023,6,14)
MAX_DAYS=366


def parse_window(start: str,end:str) -> tuple[datetime,datetime]:
    try:
        a=date.fromisoformat(start)
        b=date.fromisoformat(end)
    except (TypeError,ValueError):
        raise ValueError("Use full YYYY-MM-DD dates") from None
    if a < VALID_AFTER:
        raise ValueError("15-minute historical windows must start 2023-06-14 or later; earlier source frequency is hourly")
    if b<=a or (b-a).days>MAX_DAYS:
        raise ValueError("Require a forward window of at most 366 complete UTC days")
    if b>datetime.now(UTC).date():
        raise ValueError("Historical window cannot extend into a future date")
    return datetime.combine(a,time.min,tzinfo=UTC),datetime.combine(b,time.min,tzinfo=UTC)


def canonical(dt:str)->str:
    stamp=datetime.fromisoformat(dt.replace("Z","+00:00"))
    if stamp.tzinfo is None:raise ValueError("Source has no UTC offset")
    return stamp.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _validate_source(rows,dataset_id:int,start:datetime,end:datetime):
    expected_metric,expected_unit=DATASETS[dataset_id]
    seen=set()
    ordered=sorted(rows,key=lambda r:r.timestamp_utc)
    for row in ordered:
        if (row.source!="fingrid" or row.area!="FI" or row.dataset_id!=str(dataset_id)
            or row.metric!=expected_metric or row.unit!=expected_unit
            or row.value is None or not 0<=float(row.value)<1e6):
            raise ValueError(f"Incorrect identity, unit or value in Fingrid {dataset_id}")
        stamp=datetime.fromisoformat(canonical(row.timestamp_utc).replace("Z","+00:00"))
        finish=datetime.fromisoformat(canonical(row.interval_end_utc).replace("Z","+00:00"))
        if stamp in seen:
            raise ValueError(f"Fingrid {dataset_id} duplicate source UTC timestamp {stamp.isoformat()}")
        if finish-stamp != timedelta(minutes=15):
            raise ValueError(f"Fingrid {dataset_id} non-15-minute source duration at UTC {stamp.isoformat()} (actual minutes={(finish-stamp).total_seconds()/60:g}); no interpolation")
        if not start <= stamp < finish <= end:
            raise ValueError(f"Fingrid {dataset_id} source interval outside requested UTC window, starts {stamp.isoformat()}")
        seen.add(stamp)
    expected=int((end-start).total_seconds()/900)
    if len(ordered)!=expected:
        raise ValueError(f"Fingrid {dataset_id} incomplete: {len(ordered)} source intervals, expected {expected}; no fill")
    for i,row in enumerate(ordered):
        stamp=datetime.fromisoformat(canonical(row.timestamp_utc).replace("Z","+00:00"))
        if stamp!=start+timedelta(minutes=15*i):
            raise ValueError(f"Fingrid {dataset_id} has a missing or nonconsecutive source interval")
    return ordered


def retrieve(start:str,end:str,*,getter=None,client=None,chunk_days:int=7):
    first,last=parse_window(start,end)
    if not 1<=chunk_days<=14:raise ValueError("Chunk length must be 1..14 days")
    if getter is None and not os.environ.get("FINGRID_API_KEY"):
        raise SourceError("FINGRID_API_KEY is required privately to retrieve longer history")
    shared=client or HttpClient()
    collected={124:[],74:[]}
    for dataset_id in collected:
        cursor=first
        while cursor<last:
            final=min(cursor+timedelta(days=chunk_days),last)
            low=cursor.isoformat().replace("+00:00","Z")
            high=final.isoformat().replace("+00:00","Z")
            result=(getter(dataset_id,low,high) if getter is not None else
                    fetch(dataset_id,low,high,client=shared))
            # Fail immediately on the affected source chunk, not after a 365-day download.
            # This also avoids falsely claiming that an incomplete older series is 15-minute.
            _validate_source(result,dataset_id,cursor,final)
            collected[dataset_id].extend(result)
            cursor=final
    by_id={i:_validate_source(rows,i,first,last) for i,rows in collected.items()}
    paired=[]
    for consumption,production in zip(by_id[124],by_id[74]):
        t=canonical(consumption.timestamp_utc)
        end_consumption=canonical(consumption.interval_end_utc)
        if t!=canonical(production.timestamp_utc) or end_consumption!=canonical(production.interval_end_utc):
            raise ValueError("Fingrid 124 and 74 timestamps do not align; refusing interpolation")
        paired.append({
            "timestamp_utc":t,
            "interval_end_utc":end_consumption,
            "consumption_mwh_per_hour":format(float(consumption.value),".8f").rstrip("0").rstrip("."),
            "production_mwh_per_hour":format(float(production.value),".8f").rstrip("0").rstrip("."),
            "consumption_retrieved_at":canonical(consumption.retrieved_at),
            "production_retrieved_at":canonical(production.retrieved_at)
        })
    return paired


def write_pair(paired:list[dict],path:Path,*,window_start:str,window_end:str):
    a,b=parse_window(window_start,window_end)
    if len(paired)!=int((b-a).total_seconds()/900):
        raise ValueError("Source pairing does not span expected complete history")
    path.parent.mkdir(parents=True,exist_ok=True)
    # Atomic write; validate with PyPSA's source contract BEFORE rename.
    import tempfile
    fd,tmp=tempfile.mkstemp(prefix=".fingrid-",suffix=".csv",dir=path.parent)
    os.close(fd)
    temporary=Path(tmp)
    try:
        with temporary.open("w",encoding="utf-8",newline="") as file:
            writer=csv.DictWriter(file,fieldnames=FIELDS,lineterminator="\n")
            writer.writeheader()
            writer.writerows(paired)
        checked=load_observed(temporary)
        if len(checked)!=len(paired):
            raise ValueError("PyPSA input contract rejected part of the source window")
        digest=hashlib.sha256(temporary.read_bytes()).hexdigest()
        os.replace(temporary,path)
        return {
          "status":"source_complete",
          "classification":"observed_fingrid_national_operational_context",
          "start_utc":a.isoformat().replace("+00:00","Z"),
          "end_utc":b.isoformat().replace("+00:00","Z"),
          "complete_days":(b-a).days,
          "source_intervals":len(paired),
          "interval_hours":0.25,
          "source_datasets":[124,74],
          "source_urls":["https://data.fingrid.fi/en/datasets/124","https://data.fingrid.fi/en/datasets/74"],
          "native_units":"MWh/h = mean MW over interval",
          "csv_sha256":digest,
          "provenance":"Fingrid API key held in process environment only; row-wise UTC source and capture times retained",
          "scope_limits":"National 15-minute historical operation only; never local connectability, generation availability, or 2030 forecast",
        }
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start",required=True)
    parser.add_argument("--end",required=True,help="Exclusive end UTC date")
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--chunk-days",type=int,default=7)
    args=parser.parse_args(argv)
    raw=retrieve(args.start,args.end,chunk_days=args.chunk_days)
    metadata=write_pair(raw,args.out,window_start=args.start,window_end=args.end)
    manifest=args.out.with_suffix(".manifest.json")
    manifest.write_text(json.dumps(metadata,indent=2)+"\n",encoding="utf-8")
    print("FINGRID_HISTORY_SUMMARY_JSON="+json.dumps(metadata,sort_keys=True))


if __name__=="__main__":
    main()
