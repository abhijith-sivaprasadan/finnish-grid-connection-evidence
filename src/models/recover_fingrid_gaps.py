"""Targeted original-source recheck of three genuinely absent Fingrid 124 readings.

Manual-only. One request per missing interval, throttled > Fingrid's 2 s minimum.
NO imputation or automatic publishing of a complete source year. Credential never logged.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timedelta,timezone
import json,os,time
from pathlib import Path
import requests

from src.ingest.fingrid import DATASETS,fetch
from src.ingest.http import SourceError
from src.models.history import canonical

MISSING_124_2025=(
    "2025-01-17T17:00:00Z",
    "2025-01-17T17:45:00Z",
    "2025-07-11T16:15:00Z",
)
DATASET_ID=124
SOURCE_URL="https://data.fingrid.fi/en/datasets/124"

class NoRetryPacedClient:
    """One operator request per page; HTTP 429 is terminal in this run."""
    def __init__(self,*,session=None,spacing=5.0,sleep=time.sleep,clock=time.monotonic):
        if spacing<2.1:
            raise ValueError("Must comply with Fingrid's minimum 2-second call spacing")
        self.session=session or requests.Session()
        self.spacing=spacing
        self.sleep=sleep
        self.clock=clock
        self.last=None

    def get(self,url,**kwargs):
        if self.last is not None:
            self.sleep(max(0,self.spacing-(self.clock()-self.last)))
        self.last=self.clock()
        try:
            response=self.session.get(url,timeout=(10,40),allow_redirects=False,**kwargs)
        except requests.RequestException as err:
            raise SourceError("Fingrid source transport failure; request not retried") from None
        if response.status_code==429:
            raise SourceError("Fingrid HTTP 429, deferred without retry")
        if response.status_code!=200:
            raise SourceError(f"Fingrid HTTP {response.status_code}, no value accepted")
        return response


def exact_slot(timestamp:str)->tuple[str,str]:
    a=datetime.fromisoformat(timestamp.replace("Z","+00:00"))
    if a.tzinfo is None or a.utcoffset()!=timedelta(0) or a.minute%15 or a.second or a.microsecond:
        raise ValueError("Require UTC quarter-hour aligned timestamp")
    b=a+timedelta(minutes=15)
    return (a.strftime("%Y-%m-%dT%H:%M:%SZ"),b.strftime("%Y-%m-%dT%H:%M:%SZ"))


def verify_original_slot(timestamp:str,rows:list)->dict:
    start,end=exact_slot(timestamp)
    if not rows:
        return {"status":"still_not_published","timestamp_utc":start,"value_mwh_per_hour":None,
                "source_url":SOURCE_URL,"evidence_rows_returned":0}
    if len(rows)!=1:
        raise ValueError(f"Expected exactly one ORIGINAL source row at {start}; got {len(rows)}")
    r=rows[0]
    metric,unit=DATASETS[DATASET_ID]
    if (r.source!="fingrid" or r.area!="FI" or r.dataset_id!="124"
        or r.metric!=metric or r.unit!=unit
        or canonical(r.timestamp_utc)!=canonical(start)
        or canonical(r.interval_end_utc)!=canonical(end)):
        raise ValueError(f"Source identity/unit/time mismatch for {start}; original value rejected")
    from math import isfinite
    if r.value is None or not isfinite(float(r.value)) or float(r.value)<0:
        raise ValueError("Invalid original numerical source reading")
    return {"status":"recovered_original_fingrid_record","timestamp_utc":start,
            "interval_end_utc":end,"value_mwh_per_hour":float(r.value),"unit":unit,
            "source_url":SOURCE_URL,"source_retrieved_at_utc":canonical(r.retrieved_at),
            "evidence_rows_returned":1}


def recheck(*,get=None,client=None,slots=MISSING_124_2025)->dict:
    query=get or (lambda ts,end:fetch(124,ts,end,client=client))
    if len(slots)>3 or len(set(slots))!=len(slots):
        raise ValueError("Only up to three unique identified source gaps may be rechecked")
    states=[]
    deferred=False
    for ts in slots:
        start,end=exact_slot(ts)
        try:
            result=verify_original_slot(ts,query(start,end))
        except SourceError as exc:
            # Stop immediately. Never hammer the operator or misclassify 429 as source absent.
            states.append({"status":"request_deferred","timestamp_utc":start,
                           "reason":"Fingrid source access unavailable or rate limited; NOT an absent observation"})
            deferred=True
            break
        states.append(result)
    status=("request_deferred" if deferred else
            "all_three_originals_recovered" if len(states)==3 and all(
                x["status"]=="recovered_original_fingrid_record" for x in states)
            else "some_original_intervals_still_missing")
    return {
        "scope":"manual_original_operator_interval_recheck_only",
        "dataset_id":124,"dataset_url":SOURCE_URL,
        "requested_known_missing_utc":list(slots),
        "interval_results":states,"recheck_status":status,
        "complete_calendar_2025_source_verified":False,
        "full_year_pypsa_result_available":False,
        "modelled_substation_connection_capacity":False,
        "publication_rule":"No original source value => no fill. Even three recovered values do NOT validate all 35,040 paired annual intervals."
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--execute",action="store_true",help="Explicit network opt-in; no calls by default")
    args=p.parse_args(argv)
    if args.execute and not os.environ.get("FINGRID_API_KEY"):
        raise SourceError("Set private FINGRID_API_KEY for explicit recheck")
    client=NoRetryPacedClient() if args.execute else None
    report=recheck(client=client) if args.execute else {
      "recheck_status":"not_executed_no_source_claim",
      "requested_known_missing_utc":list(MISSING_124_2025),
      "complete_calendar_2025_source_verified":False,
      "full_year_pypsa_result_available":False}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("ORIGINAL_SOURCE_RECOVERY_JSON="+json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
