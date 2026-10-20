"""Historical SE1/SE3 commercial flows and *post-day-ahead* intraday market space.

Original Fingrid 31/32 signed FI->Sweden positive (export), negative import.
Original Fingrid 38/39 positive intraday capacity Sweden->Finland AFTER
day-ahead trade: not total transmission rights and not guaranteed physically
available energy or available headroom at any Finnish substation.

A limited counterfactual PyPSA one-bus PROJECT-ONLY import access sensitivity
uses those published 15-min market capacity observations as an assumed
ceiling for a marginal 100 MW *market-dependent* project. It does not claim
actual import rights, import dispatch, a 2030 forecast, or real outages.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from datetime import date,datetime,time,timedelta,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from src.ingest.fingrid import DATASETS,fetch
from src.ingest.http import SourceError
from src.models.recover_fingrid_gaps import NoRetryPacedClient
from src.models.history import canonical
from src.models.finland import load_observed,additional_load

IDS=(31,32,38,39)
START=date(2025,9,15)
END=date(2025,10,15)
OBSERVED_AUTUMN_SHA="3093f704484848919d83feb6c133c2e2abf2299566d5bd02a109e01b7fdec2e0"
COUNTERFACTUAL_DURATION_HOURS=(0.,2.,4.,8.)
COUNTERFACTUAL_FLEX_HALF_RANGE_MW=(0.,50.)

def parse_source(rows:list,dataset_id:int,start:datetime,end:datetime):
    expected_metric,expected_unit=DATASETS[dataset_id]
    result={}
    for obs in rows:
        if (obs.dataset_id!=str(dataset_id) or obs.source!="fingrid" or obs.area!="FI" or
            obs.metric!=expected_metric or obs.unit!=expected_unit or
            obs.source_url!=f"https://data.fingrid.fi/en/datasets/{dataset_id}"):
            raise ValueError("Incorrect real border data identity or source unit")
        stamp=datetime.fromisoformat(canonical(obs.timestamp_utc).replace("Z","+00:00"))
        finish=datetime.fromisoformat(canonical(obs.interval_end_utc).replace("Z","+00:00"))
        if (stamp<start or stamp>=end or finish-stamp!=timedelta(minutes=15)
            or stamp.minute%15 or stamp.second or stamp.microsecond):
            raise ValueError("Incompatible real border interval or frequency")
        value=float(obs.value)
        if not math.isfinite(value) or (dataset_id in (38,39) and value<0):
            raise ValueError("Nonfinite or negative unused intraday capacity")
        key=canonical(obs.timestamp_utc)
        if key in result:raise ValueError("Repeated historical cross-border observation")
        result[key]={
            "timestamp_utc":key,"interval_end_utc":canonical(obs.interval_end_utc),
            "dataset_id":dataset_id,"source_url":obs.source_url,
            "unit":expected_unit,"value":value,
            "retrieved_at_utc":canonical(obs.retrieved_at)
        }
    return result


def acquire(out:Path,*,getter=None,client=None)->dict:
    out.mkdir(parents=True,exist_ok=True)
    actual_client=client or NoRetryPacedClient(spacing=5)
    all_rows={}
    for dataset_id in IDS:
        series={}
        cursor=START
        while cursor<END:
            finish=min(cursor+timedelta(days=7),END)
            low=cursor.isoformat()+"T00:00:00Z"
            high=finish.isoformat()+"T00:00:00Z"
            chunk=(getter(dataset_id,low,high) if getter else
                   fetch(dataset_id,low,high,client=actual_client))
            validated=parse_source(chunk,dataset_id,
                datetime.combine(cursor,time.min,tzinfo=timezone.utc),
                datetime.combine(finish,time.min,tzinfo=timezone.utc))
            for key,value in validated.items():
                if key in series:raise ValueError("Repeated interval across operator chunks")
                series[key]=value
            cursor=finish
        all_rows[dataset_id]=series
        path=out/f"fingrid_{dataset_id}_border_market_2025.csv"
        with path.open("w",newline="",encoding="utf-8") as f:
            wr=csv.DictWriter(f,fieldnames=("timestamp_utc","interval_end_utc",
               "dataset_id","source_url","unit","value","retrieved_at_utc"))
            wr.writeheader()
            wr.writerows(series[k] for k in sorted(series))
        print("BORDER_OPERATOR_SOURCE_CAPTURE_JSON="+json.dumps({
          "dataset_id":dataset_id,"rows":len(series),
          "sha256":hashlib.sha256(path.read_bytes()).hexdigest()
        },sort_keys=True))
    day_coverage={}
    valid_days=[]
    d=START
    while d<END:
        times=[datetime.combine(d,time.min,tzinfo=timezone.utc).replace(tzinfo=timezone.utc)
               +timedelta(minutes=15*i) for i in range(96)]
        timestamps=[t.strftime("%Y-%m-%dT%H:%M:%S.%fZ") for t in times]
        gaps={str(dataset_id):[t for t in timestamps if t not in all_rows[dataset_id]]
              for dataset_id in IDS}
        good=all(not v for v in gaps.values())
        day_coverage[d.isoformat()]={
            "original_source_complete":good,
            "missing_slots_utc_by_dataset":gaps
        }
        if good:valid_days.append(d)
        d+=timedelta(days=1)
    # Select longest consecutive complete original-source segment;
    # never concatenate gaps across a battery state of charge.
    runs=[]
    for d in valid_days:
        if runs and d==runs[-1][-1]+timedelta(days=1):runs[-1].append(d)
        else:runs.append([d])
    runs.sort(key=lambda x:(-len(x),x[0]))
    chosen=runs[0] if runs else []
    meta={
      "source_kind":"observed_Fingrid_commercial_flow_and_intraday_market_capacity",
      "source_year":2025,"original_observation_datasets":list(IDS),
      "dataset_roles":{
        "31":"signed FI-SE1 commercial net export (+ export, - import), MW",
        "32":"signed FI-SE3 commercial net export (+ export, - import), MW",
        "38":"unused intraday market capacity SE1->FI after day-ahead MW",
        "39":"unused intraday market capacity SE3->FI after day-ahead MW"},
      "source_urls":[f"https://data.fingrid.fi/en/datasets/{i}" for i in IDS],
      "original_records_per_dataset":{str(i):len(all_rows[i]) for i in IDS},
      "source_csv_sha256":{
        str(i):hashlib.sha256((out/f"fingrid_{i}_border_market_2025.csv").read_bytes()).hexdigest()
        for i in IDS},
      "source_day_coverage":day_coverage,
      "longest_complete_consecutive_source_days":len(chosen),
      "selected_utc":{ "start":chosen[0].isoformat()+"T00:00:00Z",
                        "end_exclusive":(chosen[-1]+timedelta(days=1)).isoformat()+"T00:00:00Z"}
                        if chosen else None,
      "published_market_capacity_is_not_physical_connection_headroom":True,
      "no_inference_of_actual_import_rights":True,
      "annual_import_capacity_confirmed":False
    }
    (out/"border_source_inventory_2025.json").write_text(json.dumps(meta,indent=2)+"\n")
    return {"sources":all_rows,"chosen":chosen,"manifest":meta}


def genuine_context(inventory:dict,autumn_csv:Path,out:Path):
    autumn_sha=hashlib.sha256(autumn_csv.read_bytes()).hexdigest()
    if autumn_sha!=OBSERVED_AUTUMN_SHA:
        raise ValueError("The 2025 autumn national demand-production CSV does not match verified source SHA")
    observed=load_observed(autumn_csv)
    days=inventory["chosen"]
    if len(days)<14:
        return {"state":"insufficient_matched_operator_source","minimum_days":14,
                "source_manifest":inventory["manifest"],
                "model_results":[],"reason":"Actual cross-border observations did not cover at least 14 contiguous UTC days"}
    start=datetime.combine(days[0],time.min,tzinfo=timezone.utc)
    finish=datetime.combine(days[-1]+timedelta(days=1),time.min,tzinfo=timezone.utc)
    matched=observed[(observed.index>=start.replace(tzinfo=None))&
                     (observed.index<finish.replace(tzinfo=None))]
    if len(matched)!=len(days)*96:
        raise ValueError("National source archive missing matching original 15-minute rows")
    selection=[]
    for row in matched.itertuples():
        ts=canonical(row.timestamp_utc)
        data=[inventory["sources"][id][ts]["value"] for id in IDS]
        selection.append({"timestamp_utc":ts,
          "commercial_export_FI_SE1_mw":data[0],
          "commercial_export_FI_SE3_mw":data[1],
          "unused_intraday_import_SE1_FI_mw":data[2],
          "unused_intraday_import_SE3_FI_mw":data[3],
          "unused_intraday_import_two_swedish_borders_mw":data[2]+data[3]})
    caps=pd.Series([r["unused_intraday_import_two_swedish_borders_mw"] for r in selection],index=matched.index)
    import pypsa
    summaries=[]
    for flex in COUNTERFACTUAL_FLEX_HALF_RANGE_MW:
        for hours in COUNTERFACTUAL_DURATION_HOURS:
            project_load=additional_load(matched,"flexible_100mw" if flex else "flat_100mw",flex_span_mw=flex)
            network=pypsa.Network()
            network.set_snapshots(pd.DatetimeIndex(matched.index))
            network.snapshot_weightings.loc[:,:]=0.25
            network.add("Bus","abstract_incremental_project")
            network.add("Load","assumed_project_100mw",bus="abstract_incremental_project",p_set=project_load)
            name="hypothetical_access_to_unused_intraday_capacity"
            available=float(caps.max())
            network.add("Generator",name,bus="abstract_incremental_project",
                        p_nom=max(1.,available),marginal_cost=1.,
                        p_max_pu=0.)
            network.generators_t.p_max_pu[name]=caps/max(1.,available)
            network.add("Generator","penalty_relaxation_not_actual_outage",
                        bus="abstract_incremental_project",p_nom=250.,marginal_cost=10000.)
            if hours:
                network.add("StorageUnit","hypothetical_project_battery",bus="abstract_incremental_project",
                  p_nom=100.,max_hours=hours,
                  efficiency_store=float(np.sqrt(.9)),efficiency_dispatch=float(np.sqrt(.9)),
                  cyclic_state_of_charge=True,marginal_cost=0.01)
            solver_status,termination=network.optimize(solver_name="highs",log_to_console=False)
            if solver_status!="ok" or termination!="optimal":raise AssertionError("Market-bound PyPSA solver failed")
            generation=network.generators_t.p
            supply=generation[name].astype(float)
            relaxed=generation["penalty_relaxation_not_actual_outage"].astype(float)
            if hours:
                charge=network.storage_units_t.p_store["hypothetical_project_battery"].astype(float)
                discharge=network.storage_units_t.p_dispatch["hypothetical_project_battery"].astype(float)
            else:
                charge=pd.Series(0.,index=matched.index)
                discharge=pd.Series(0.,index=matched.index)
            error=float((supply+relaxed+discharge-charge-project_load).abs().max())
            if error>1e-5 or any(supply>caps+1e-5):raise AssertionError("Dispatch violates source-bounded market sensitivity")
            energy=lambda x:round(float(x.sum()*.25),4)
            if abs(energy(project_load)-len(matched)*.25*100)>1e-5:
                raise AssertionError("Project load must retain exactly 100 MW period-mean")
            summaries.append({
              "assumed_project_load_mw":100.,"flex_half_span_mw_assumed":flex,
              "battery_power_mw_assumed":100. if hours else 0.,
              "battery_duration_h_assumed":hours,"battery_round_trip_efficiency_assumed":0.9,
              "source_market_capacity_definition":"Fingrid unused INTRADAY import capacity SE1+SE3 after day-ahead allocation, MW; NOT total physical grid capacity",
              "model_project_energy_mwh":energy(project_load),
              "source_market_access_upper_bound_mwh":energy(caps),
              "counterfactual_import_access_used_mwh":energy(supply),
              "modelled_unserved_project_relaxation_mwh":energy(relaxed),
              "max_power_balance_error_mw":error,
              "solver_status":solver_status,"solver_termination":termination
            })
    payload={
      "status":"source_verified_empirical_market_availability_counterfactual",
      "data_kind":"historical_operator_data_plus_model_scenario",
      "historical_source_datasets":[124,74,31,32,38,39],
      "national_source_sha256":autumn_sha,
      "source_manifest":inventory["manifest"],
      "selected_days":len(days),"selected_intervals":len(selection),
      "observed_commercial_flow_statistics":{
        "signed_commercial_FI_SE1_mean_mw":round(float(np.mean([x["commercial_export_FI_SE1_mw"] for x in selection])),3),
        "signed_commercial_FI_SE3_mean_mw":round(float(np.mean([x["commercial_export_FI_SE3_mw"] for x in selection])),3),
        "intraday_capacity_2_sweden_borders_mw_min":round(float(caps.min()),3),
        "intraday_capacity_2_sweden_borders_mw_median":round(float(caps.median()),3),
        "intraday_capacity_2_sweden_borders_mw_max":round(float(caps.max()),3),
        "share_intervals_with_unused_intraday_SE_to_FI_above_100mw":round(float((caps>=100).mean()),5)
      },
      "scenarios":summaries,
      "interpretation":"Observed 2025 border flows are descriptive history. Solver measures a wholly conditional new-load counterfactual if it could participate in unused SE1/SE3 intraday import market space; source capacity is NOT actual network connection headroom or import right.",
      "limitations":[
        "Fingrid commercial flow is not identical to measured physical border exchange, and positive is Finnish export.",
        "Unused intraday import space after day-ahead allocation is not total net transfer capacity, and cannot be treated as total available energy, reliable plant output or actual new project import rights.",
        "Only two Swedish bidding zone borders are represented; excludes Estonia, Norway, domestic transmission congestion and locational capacity.",
        "Project-only market-access counterfactual does not model Finland national residual or actual network topology; do not compare its penalty metric directly to national single-bus stress results.",
        "Battery and flexible load are hypothetical, flex schedule uses historical hindsight, and cyclic storage over this observed window does not model forecast operations.",
        "No source data or model can establish 2030 connection capacity at any named Fingrid grid point."
      ]
    }
    out.mkdir(parents=True,exist_ok=True)
    joined=out/"verified_border_source_15min.csv"
    with joined.open("w",newline="",encoding="utf-8") as f:
        wr=csv.DictWriter(f,fieldnames=list(selection[0]))
        wr.writeheader()
        wr.writerows(selection)
    payload["joined_source_sha256"]=hashlib.sha256(joined.read_bytes()).hexdigest()
    (out/"verified_market_bound_model.json").write_text(json.dumps(payload,indent=2)+"\n")
    print("VERIFIED_BORDER_MARKET_MODEL_JSON="+json.dumps({
      "days":len(days),"cases":len(summaries),
      "observed_market_median_mw":payload["observed_commercial_flow_statistics"]["intraday_capacity_2_sweden_borders_mw_median"],
      "source_sha256":payload["joined_source_sha256"],"status":payload["status"]
    },sort_keys=True))
    return payload


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--autumn-csv",type=Path,required=True)
    p.add_argument("--outdir",type=Path,required=True)
    args=p.parse_args()
    source=acquire(args.outdir)
    result=genuine_context(source,args.autumn_csv,args.outdir)
    if result["status"]!="source_verified_empirical_market_availability_counterfactual":
        (args.outdir/"border_source_incomplete.json").write_text(json.dumps(result,indent=2)+"\n")
        print("BORDER_OPERATOR_SOURCE_INSUFFICIENT="+json.dumps({"days":source["manifest"]["longest_complete_consecutive_source_days"]}))
        raise ValueError("Border market source was insufficient; no solver result can be published")


if __name__=="__main__":
    main()
