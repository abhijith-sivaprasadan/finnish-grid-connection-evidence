"""Two separately validated 27-day PyPSA studies from immutable 2025 Fingrid journal.

Battery energy (2/4/8h) and flex (0/50 MW) are actual OPTIMIZATION variants,
never synthetic Fingrid observations. Each source window is contiguous UTC.
All imposed 1/1.5/2 GW national balancing limits remain INVENTED stress
bounds pending correctly aligned genuine border-capacity observations.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime,timedelta,timezone
from pathlib import Path

from src.models.annual_journal import windows,chunk_key,load_chunk
from src.models.history import canonical,write_pair
from src.models.finland import load_observed,solve_case

WINDOWS={
    "winter27":("2025-01-18","2025-02-14"),
    "latewinter27":("2025-02-15","2025-03-14")
}
BALANCING_ASSUMED=(1000.,1500.,2000.)
FLEX_HALF_SPANS=(0.,50.)
BATTERY_HOURS=(2.,4.,8.)

def verified_window_rows(journal:Path,start:str,end:str)->list[dict]:
    low=datetime.fromisoformat(start+"T00:00:00+00:00")
    high=datetime.fromisoformat(end+"T00:00:00+00:00")
    readings={124:{},74:{}}
    for a,b in windows():
        if not (a<high and b>low):continue
        for id in (124,74):
            content=load_chunk(journal/(chunk_key(id,a,b)+".json"),id,a,b)
            for item in content["original_rows"]:
                stamp=canonical(item["timestamp_utc"])
                if low<=datetime.fromisoformat(stamp.replace("Z","+00:00"))<high:
                    if stamp in readings[id]:raise ValueError("Duplicate source interval across chunks")
                    readings[id][stamp]=item
    expected=int((high-low).total_seconds()/900)
    if any(len(readings[id])!=expected for id in (124,74)):
        raise ValueError("Source interval gap in selected 27-day window: no interpolation or zero")
    paired=[]
    for i in range(expected):
        dt=low+timedelta(minutes=15*i)
        ts=dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        finish=(dt+timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        if ts not in readings[124] or ts not in readings[74]:
            raise ValueError("Source gap in claimed contiguous 27-day window")
        c,p=readings[124][ts],readings[74][ts]
        if canonical(c["interval_end_utc"])!=finish or canonical(p["interval_end_utc"])!=finish:
            raise ValueError("Original Fingrid source 124/74 end times do not match")
        paired.append({
          "timestamp_utc":ts,"interval_end_utc":finish,
          "consumption_mwh_per_hour":str(c["value"]),
          "production_mwh_per_hour":str(p["value"]),
          "consumption_retrieved_at":canonical(c["retrieved_at"]),
          "production_retrieved_at":canonical(p["retrieved_at"])
        })
    return paired


def execute(journal:Path,outdir:Path,*,skip_solves=False):
    outdir.mkdir(parents=True,exist_ok=True)
    studies=[]
    for name,(start,end) in WINDOWS.items():
        original=verified_window_rows(journal,start,end)
        source=outdir/(name+"_original_fingrid.csv")
        manifest=write_pair(original,source,window_start=start,window_end=end)
        loaded=load_observed(source)
        if len(loaded)!=2592 or manifest["source_intervals"]!=2592:
            raise AssertionError("27-day original source history expected")
        entry={
          "window":name,"source_start_utc":start+"T00:00:00Z",
          "source_end_utc_exclusive":end+"T00:00:00Z",
          "complete_days":27,"verified_original_pair_count":2592,
          "source_sha256":manifest["csv_sha256"],"source_manifest":manifest,
          "model_results":[],"model_baselines":[],"solver_completed":False
        }
        if not skip_solves:
            baseline={}
            for cap in BALANCING_ASSUMED:
                base,_=solve_case(loaded,"observed_reference",balancing_limit_mw=cap)
                if base["solver_status"]!="ok" or base["termination"]!="optimal":
                    raise AssertionError("Reference optimization did not solve")
                baseline[cap]=base["modelled_shortfall_under_assumption_mwh"]
                entry["model_baselines"].append({"balancing_cap_mw_assumed":cap,
                    "reference_penalty_slack_mwh":baseline[cap]})
            # Only solve zero-battery scenarios once; battery duration is
            # meaningless for those cases. With battery, solve 2/4/8 h.
            for cap in BALANCING_ASSUMED:
                for span in FLEX_HALF_SPANS:
                    for installed in (False,True):
                        for duration in (BATTERY_HOURS if installed else (0.,)):
                            scenario=("flexible_100mw" if span else "flat_100mw")
                            if installed:scenario+="_with_battery"
                            result,_=solve_case(loaded,scenario,
                                balancing_limit_mw=cap,flex_span_mw=span,
                                battery_power_mw=100.,battery_hours=duration if installed else 4.)
                            if (result["termination"]!="optimal" or result["solver_status"]!="ok" or
                                result["max_model_balance_error_mw"]>1e-5 or
                                abs(result["new_demand_mwh"]-64800)>1e-5):
                                raise AssertionError("Mathematically invalid 27-day sensitivity result")
                            entry["model_results"].append({
                              "balancing_cap_mw_assumed":cap,
                              "load_flex_half_span_mw_assumed":span,
                              "battery_power_mw_assumed":100. if installed else 0.,
                              "battery_duration_hours_assumed":duration,
                              "battery_energy_mwh_assumed":100*duration if installed else 0.,
                              "incremental_penalty_slack_mwh":round(
                                result["modelled_shortfall_under_assumption_mwh"]-baseline[cap],4),
                              "total_model_penalty_slack_mwh":result["modelled_shortfall_under_assumption_mwh"],
                              "scenario":scenario,
                              "solver_status":result["solver_status"],
                              "solver_termination":result["termination"],
                              "max_balance_error_mw":result["max_model_balance_error_mw"],
                              "project_energy_mwh":result["new_demand_mwh"]
                            })
            if len(entry["model_baselines"])!=3 or len(entry["model_results"])!=24:
                raise AssertionError("Each verified window must have 3 reference + 24 model solutions")
            entry["solver_completed"]=True
        studies.append(entry)
        print("VERIFIED_LONG_WINDOW_JSON="+json.dumps({
            "window":name,"source_sha256":entry["source_sha256"],
            "source_pairs":2592,"modelled_cases":len(entry["model_results"]),
            "baseline_cases":len(entry["model_baselines"])
        },sort_keys=True))
    payload={
      "publication_status":"source_and_optimization_verified" if not skip_solves else "source_verified_no_model_run",
      "classification":"model_scenario_not_fingrid_observation",
      "historical_source_datasets":[124,74],
      "historical_journal_run":"https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39418640253",
      "journal_artifact_id":12262681192,
      "full_2025_source_complete":False,
      "model_is_fingrid_operator_capacity":False,
      "long_windows":studies,
      "scenario_assumptions":{
        "nominal_project_added_mw":100.,
        "assumed_national_balancing_bounds_mw":list(BALANCING_ASSUMED),
        "hindsight_flex_half_spans_mw":list(FLEX_HALF_SPANS),
        "hypothetical_battery_power_mw":100.,
        "hypothetical_battery_durations_hours":list(BATTERY_HOURS),
        "round_trip_efficiency_assumed":0.90,
        "fully_continuous_battery_state_of_charge_per_window":True
      },
      "limitations":[
        "These are two independently modelled 27-day historical source windows, not a continuous 54-day storage schedule or an annual dispatch study.",
        "Optimized flexibility is hindsight-guided using actual historical source residuals, not forecast or operating capability.",
        "The 1000/1500/2000 MW assumed national balancing bounds remain purely hypothetical and are NOT real Fingrid import/export rights.",
        "Shortfall represents invented relaxation of an assumed balance model, not measured blackouts, customer unserved electricity, or actual congestion.",
        "Battery power, duration, round-trip efficiency and cyclic state assumptions are hypothetical; no economic dispatch prices or validated local topology.",
        "Cannot support a 2030 local connection-capacity decision."
      ]
    }
    (outdir/"verified_long_windows_2025.json").write_text(json.dumps(payload,indent=2)+"\n")
    return payload


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--journal",type=Path,required=True)
    p.add_argument("--outdir",type=Path,required=True)
    p.add_argument("--source-only",action="store_true")
    a=p.parse_args()
    execute(a.journal,a.outdir,skip_solves=a.source_only)


if __name__=="__main__":
    main()
