"""Fingrid 124/74 coverage QA and fair matched-window PyPSA sensitivity.

Only strictly present 15-minute original source intervals enter PyPSA.
Days with ANY missing or incompatible source interval are excluded.
A fixed, equal-length consecutive subwindow is used in each season.
"""
from __future__ import annotations
from datetime import datetime,date,time,timedelta,timezone
from pathlib import Path
import json,hashlib,math
import numpy as np

from src.ingest.fingrid import DATASETS,fetch
from src.ingest.http import HttpClient,SourceError
from src.models.history import canonical,write_pair
from src.models.seasons import SEASON_WINDOWS
from src.models.sweep import run_sweep

UTC=timezone.utc
EXPECTED_EACH_DAY=96


def audit_window(start: str,end: str, *,getter=None, client=None,chunk_days=7)->dict:
    first=datetime.combine(date.fromisoformat(start),time.min,tzinfo=UTC)
    last=datetime.combine(date.fromisoformat(end),time.min,tzinfo=UTC)
    assert first<last
    original={}
    source_errors={}
    shared=client or HttpClient()
    for source_id in (124,74):
        observed={}
        exceptions=[]
        cursor=first
        while cursor<last:
            stop=min(cursor+timedelta(days=chunk_days),last)
            low=cursor.isoformat().replace("+00:00","Z")
            high=stop.isoformat().replace("+00:00","Z")
            try:
                rows=(getter(source_id,low,high) if getter is not None else
                     fetch(source_id,low,high,client=shared))
            except SourceError as error:
                # Fail the whole source: a transport failure is not an observed gap.
                raise SourceError(f"Fingrid {source_id} historical source request failed; no seasonal screening") from error
            metric,unit=DATASETS[source_id]
            for r in rows:
                if (r.source!="fingrid" or r.area!="FI" or
                    r.dataset_id!=str(source_id) or r.metric!=metric or r.unit!=unit or
                    not math.isfinite(float(r.value)) or float(r.value)<0):
                    raise ValueError(f"Fingrid {source_id} unexpected source identity or unit")
                t=datetime.fromisoformat(canonical(r.timestamp_utc).replace("Z","+00:00"))
                finish=datetime.fromisoformat(canonical(r.interval_end_utc).replace("Z","+00:00"))
                if not first<=t<last:
                    raise ValueError(f"Fingrid {source_id} out-of-window source reading {t.isoformat()}")
                if finish-t!=timedelta(minutes=15):
                    raise ValueError(f"Fingrid {source_id} non-15-minute reading at {t.isoformat()} (no interpolation)")
                if t in observed:
                    raise ValueError(f"Fingrid {source_id} duplicated a reading at {t.isoformat()}")
                observed[t]=r
            cursor=stop
        original[source_id]=observed
        source_errors[source_id]=exceptions
    days=[]
    cursor=first
    complete=[]
    while cursor<last:
        expected=[cursor+timedelta(minutes=15*i) for i in range(EXPECTED_EACH_DAY)]
        missing={
          str(source_id):[x.strftime("%Y-%m-%dT%H:%M:%SZ") for x in expected if x not in original[source_id]]
          for source_id in (124,74)
        }
        complete_day=not missing["124"] and not missing["74"]
        entry={
          "date_utc":cursor.date().isoformat(),
          "fingrid_124_intervals":96-len(missing["124"]),
          "fingrid_74_intervals":96-len(missing["74"]),
          "paired_source_complete":complete_day,
          "missing_utc_intervals_by_dataset":missing
        }
        days.append(entry)
        if complete_day:complete.append(cursor.date())
        cursor+=timedelta(days=1)
    return {
      "start_utc":start+"T00:00:00Z","end_utc":end+"T00:00:00Z",
      "days":days,"complete_dates":complete,"observed":original,
      "missing_source_intervals":{
        str(i):sum(len(d["missing_utc_intervals_by_dataset"][str(i)]) for d in days) for i in (124,74)
      }
    }


def runs(complete_dates:list[date])->list[list[date]]:
    ordered=sorted(set(complete_dates))
    groups=[]
    for d in ordered:
        if groups and d==groups[-1][-1]+timedelta(days=1):
            groups[-1].append(d)
        else:
            groups.append([d])
    return sorted(groups,key=lambda g:(-len(g),g[0]))


def selected_block(audits:dict[str,dict],*,max_days=14,min_days=3)->dict[str,list[date]]:
    if not 1<=min_days<=max_days<=30:
        raise ValueError("Specify min/max matched window length 1..30")
    lengths={label:len(runs(audit["complete_dates"])[0]) if runs(audit["complete_dates"]) else 0
             for label,audit in audits.items()}
    common=min(max_days,*lengths.values())
    if common<min_days:
        raise ValueError(f"No {min_days}-day complete matched windows available; longest runs by season: {lengths}")
    return {label:runs(audit["complete_dates"])[0][:common] for label,audit in audits.items()}


def paired_series(audit:dict,dates:list[date])->list[dict]:
    selected=[]
    for day in dates:
        start=datetime.combine(day,time.min,tzinfo=UTC)
        for slot in range(96):
            t=start+timedelta(minutes=15*slot)
            if t not in audit["observed"][124] or t not in audit["observed"][74]:
                raise ValueError("Selected matched date has missing original interval; refusing synthetic fill")
            consumption=audit["observed"][124][t]
            production=audit["observed"][74][t]
            selected.append({
              "timestamp_utc":canonical(consumption.timestamp_utc),
              "interval_end_utc":canonical(consumption.interval_end_utc),
              "consumption_mwh_per_hour":format(float(consumption.value),".8f").rstrip("0").rstrip("."),
              "production_mwh_per_hour":format(float(production.value),".8f").rstrip("0").rstrip("."),
              "consumption_retrieved_at":canonical(consumption.retrieved_at),
              "production_retrieved_at":canonical(production.retrieved_at)
            })
    return selected


def study(output_dir:Path,*,getter=None,min_days=3,max_days=14)->dict:
    output_dir.mkdir(parents=True,exist_ok=True)
    audits={label:audit_window(*bounds,getter=getter) for label,bounds in SEASON_WINDOWS.items()}
    coverage={
      label:{
        "date_window_utc":[a["start_utc"],a["end_utc"]],
        "total_days":len(a["days"]),
        "days_with_both_sources_complete":len(a["complete_dates"]),
        "missing_intervals_by_dataset":a["missing_source_intervals"],
        "day_by_day":[dict(d) for d in a["days"]],
        "longest_consecutive_complete_run_days":len(runs(a["complete_dates"])[0]) if runs(a["complete_dates"]) else 0
      } for label,a in audits.items()
    }
    (output_dir/"seasonal_source_coverage_2025.json").write_text(json.dumps(coverage,indent=2)+"\n")
    # Coverage must always be published even if the model cannot run at equal durations.
    try:
        selected=selected_block(audits,max_days=max_days,min_days=min_days)
    except ValueError as error:
        report={"status":"insufficient_source_coverage","error":str(error),"model_results":[],
                "coverage":coverage,"annual_coverage_confirmed":False}
        (output_dir/"matched_windows_report.json").write_text(json.dumps(report,indent=2)+"\n")
        print("MATCHED_SEASONS_NO_SOLVE_JSON="+json.dumps({"reason":str(error)}))
        return report
    records=[]
    for label,days in selected.items():
        source=output_dir/f"fi_{label}_matched_2025.csv"
        first,end=days[0].isoformat(),(days[-1]+timedelta(days=1)).isoformat()
        manifest=write_pair(paired_series(audits[label],days),source,
                            window_start=first,window_end=end)
        solved=run_sweep(source,output=output_dir/f"fi_{label}_matched_pypsa.json")
        if solved["observed_input_sha256"]!=manifest["csv_sha256"] or len(solved["results"])!=12:
            raise AssertionError("Matched season model output does not align with original source")
        if any(r["solver_status"]!="ok" or r["solver_termination"]!="optimal" or
               r["max_balance_error_mw"]>1e-5 or
               r["added_load_energy_mwh"]!=len(days)*24*100 for r in solved["results"]):
            raise AssertionError("Model did not solve optimal energy-neutral matched season")
        records.append({
          "season":label,
          "source_window_start_utc":first+"T00:00:00Z",
          "source_window_end_utc":end+"T00:00:00Z",
          "complete_contiguous_days":len(days),
          "original_fingrid_15min_pairs":len(days)*96,
          "source_input_sha256":manifest["csv_sha256"],
          "scenarios":solved["results"]
        })
    comparison=[]
    for cap in (1000.0,1500.0,2000.0):
      for flex in (0.0,50.0):
       for power in (0.0,100.0):
        vals={r["season"]:next(x["incremental_shortfall_vs_reference_mwh"] for x in r["scenarios"]
               if x["balancing_limit_mw_assumed"]==cap and x["flex_half_range_mw_assumed"]==flex and
               x["battery_power_mw_assumed"]==power) for r in records}
        a=list(vals.values())
        comparison.append({
          "assumed_balancing_limit_mw":cap,
          "assumed_flexibility_half_span_mw":flex,
          "assumed_battery_power_mw":power,
          "incremental_modelled_penalty_shortfall_mwh_by_season":vals,
          "descriptive_min_mwh":round(min(a),4),
          "descriptive_median_mwh":round(float(np.median(a)),4),
          "descriptive_max_mwh":round(max(a),4),
          "descriptive_range_mwh":round(max(a)-min(a),4),
        })
    report={
      "status":"three_seasons_source_and_solver_verified",
      "data_kind":"model_scenario",
      "original_source_datasets":[124,74],
      "source_urls":["https://data.fingrid.fi/en/datasets/124",
                     "https://data.fingrid.fi/en/datasets/74"],
      "study_year":2025,
      "annual_coverage_confirmed":False,
      "sample_selection":"Longest complete consecutive-day run in each predeclared 30-day season; common equal-length prefix capped at 14 days, minimum 3; source gaps never filled.",
      "equal_comparison_days":len(selected["winter"]),
      "coverage":coverage,"matched_season_solutions":records,"parameter_comparison":comparison,
      "limitations":[
       "Only documented original complete 15-minute source readings are used; unmatched intervals are excluded without filling or smoothing.",
       "Matched samples are selected after inspecting missingness; the coverage and selection rule are explicit and may bias seasonal representativeness.",
       "Three small source-complete periods are NOT full meteorological seasons, a complete annual model or a prediction for 2030.",
       "The optimization's penalty slack is hypothetical, NOT observed Finnish unserved electricity or blackouts.",
       "Balancing ceilings 1000/1500/2000 MW are assumed sensitivity inputs NOT Fingrid import limits, transmission headroom or connection rights.",
       "No grid topology, local capacity or market-price inference is provided.",
       "Battery and hindsight-based flexible daily project schedule are explicitly hypothetical."
      ]
    }
    (output_dir/"matched_windows_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MATCHED_SEASONS_VERIFIED_JSON="+json.dumps({
      "days_each":len(selected["winter"]),
      "seasons":[{"season":r["season"],"start":r["source_window_start_utc"],
                  "end":r["source_window_end_utc"],"sha":r["source_input_sha256"]}
                 for r in records],
      "source_day_coverage":{s:{"complete_days":x["days_with_both_sources_complete"],
                                "missing_124":x["missing_intervals_by_dataset"]["124"],
                                "missing_74":x["missing_intervals_by_dataset"]["74"]}
                             for s,x in coverage.items()},
      "solves":sum(len(r["scenarios"]) for r in records)
    },sort_keys=True))
    return report


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--min-days",type=int,default=3)
    p.add_argument("--max-days",type=int,default=14)
    a=p.parse_args()
    study(a.output_dir,min_days=a.min_days,max_days=a.max_days)


if __name__=="__main__":
    main()
