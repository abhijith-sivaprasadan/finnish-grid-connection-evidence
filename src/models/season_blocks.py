"""Independent 30-day season retrieval and PyPSA stress comparison.

A failure in one historical season must not poison source-validated seasons.
No absent period, partial source, or non-15-minute reading is imputed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from src.ingest.http import SourceError
from src.models.history import retrieve, write_pair
from src.models.seasons import SEASON_WINDOWS
from src.models.sweep import run_sweep

def execute(output_dir:Path, *,getter=None, solve=True)->dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    seasons=[]
    for label,(start,end) in SEASON_WINDOWS.items():
        record={"season":label,"start_utc":start+"T00:00:00Z","end_utc":end+"T00:00:00Z",
                "expected_days":30,"expected_intervals":2880}
        try:
            pairs=retrieve(start,end,getter=getter)
            source=output_dir/f"fingrid_{label}_2025_15min.csv"
            manifest=write_pair(pairs,source,window_start=start,window_end=end)
        except (ValueError,SourceError) as error:
            record.update({"status":"source_incomplete_or_incompatible","source_complete":False,
                           "diagnostic":str(error)[:500], "solver_run":False})
            seasons.append(record)
            print(f"SEASON_SOURCE_REJECTED_JSON="+json.dumps(record,sort_keys=True))
            continue
        record.update({"status":"source_complete","source_complete":True,"source_manifest":manifest,
                       "source_sha256":manifest["csv_sha256"]})
        if solve:
            result=run_sweep(source,output=output_dir/f"pypsa_{label}_2025.json")
            if (result["observed_input_sha256"]!=record["source_sha256"] or
                len(result["results"])!=12 or len(result["baselines"])!=3 or
                any(x["solver_status"]!="ok" or x["solver_termination"]!="optimal"
                    or x["max_balance_error_mw"]>1e-5 or x["added_load_energy_mwh"]!=72000
                    for x in result["results"])):
                raise AssertionError(f"Solver verification failed for {label}")
            record.update({"status":"source_and_solver_verified","solver_run":True,
                           "scenarios":result["results"],
                           "baselines":result["baselines"]})
        else:
            record["solver_run"]=False
        seasons.append(record)
        print("SEASON_VERIFIED_JSON="+json.dumps({
          "season":label,"source_sha256":record["source_sha256"],
          "modelled_cases":len(record.get("scenarios",[]))
        },sort_keys=True))
    successful=[s for s in seasons if s["source_complete"] and s["solver_run"]]
    comparisons=[]
    for cap in (1000,1500,2000):
        for span in (0,50):
            for battery in (0,100):
                vals={
                  s["season"]:next(x["incremental_shortfall_vs_reference_mwh"] for x in s["scenarios"]
                  if x["balancing_limit_mw_assumed"]==cap and
                  x["flex_half_range_mw_assumed"]==span and
                  x["battery_power_mw_assumed"]==battery)
                  for s in successful
                }
                comparison={
                    "assumed_balancing_limit_mw":cap,
                    "assumed_flex_half_span_mw":span,
                    "assumed_battery_power_mw":battery,
                    "incremental_model_penalty_shortfall_mwh_by_validated_season":vals
                }
                if vals:
                    arr=list(vals.values())
                    comparison.update({
                        "sample_count":len(arr),
                        "descriptive_min_mwh":min(arr),
                        "descriptive_median_mwh":round(float(np.median(arr)),4),
                        "descriptive_max_mwh":max(arr),
                        "descriptive_range_mwh":round(max(arr)-min(arr),4)
                    })
                else:
                    comparison["sample_count"]=0
                comparisons.append(comparison)
    study={
      "publication_state":"three_seasons_verified" if len(successful)==3 else "partial_seasonal_source_coverage",
      "research_scope":"Three prespecified 30-day seasons; no source inference from rejected windows",
      "source_datasets":[124,74],
      "source_urls":["https://data.fingrid.fi/en/datasets/124","https://data.fingrid.fi/en/datasets/74"],
      "observed_year":2025,
      "valid_season_count":len(successful),
      "rejected_season_count":3-len(successful),
      "historical_seasons":seasons,
      "parameter_comparisons":comparisons,
      "annual_2025_complete":False,
      "annual_scope_note":"This independent fallback does not assert complete calendar-year 2025 source coverage; the strict annual audit must pass separately.",
      "model_data_kind":"model_scenario",
      "physical_grid_feasibility_verified":False,
      "limitations":[
       "Missing or incompatible source intervals remain rejected, never filled or resampled.",
       "Three selected monthly seasons are not a full-year optimization or sampling confidence interval.",
       "All 1000/1500/2000 MW balancing caps are hypothetical, NOT actual Finnish import or connection capacity.",
       "High-penalty slack is an optimization construct, NOT observed outages.",
       "Flexible schedule uses hindsight knowledge of observed residual demand.",
       "No local transmission topology, substation headroom, queue or 2030 forecast."
      ]
    }
    path=output_dir/"audited_independent_seasons_2025.json"
    path.write_text(json.dumps(study,indent=2)+"\n",encoding="utf-8")
    print("INDEPENDENT_SEASONS_SUMMARY_JSON="+json.dumps({
      "status":study["publication_state"],"accepted":[s["season"] for s in successful],
      "rejected":[{"season":s["season"],"diagnostic":s["diagnostic"]}
                  for s in seasons if not s["source_complete"]],
      "verified_cases":sum(len(s["scenarios"]) for s in successful)
    },sort_keys=True))
    return study


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",required=True,type=Path)
    args=parser.parse_args()
    execute(args.output_dir)


if __name__=="__main__":
    main()
