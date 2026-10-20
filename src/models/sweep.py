"""Source-validated 100 MW national PyPSA sensitivity grid.

Each solve is a real PyPSA + HiGHS linear optimisation; no synthetic
demand or generation chronology. All changed limits, battery and load
flexibility are explicitly hypothetical test parameters.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re

from src.models.finland import load_observed, solve_case, MODEL_VERSION


def csv_list(text:str,*,allow_zero:bool=False)->list[float]:
    if not re.fullmatch(r"\d+(?:\.\d+)?(?:,\d+(?:\.\d+)?)*",text):
        raise ValueError("Parameter grid must contain comma-separated finite nonnegative numbers")
    values=[float(s) for s in text.split(",")]
    if len(values)>5 or len(set(values))!=len(values):
        raise ValueError("Use up to five distinct values per parameter")
    if any(v<0 if allow_zero else v<=0 for v in values):
        raise ValueError("Model parameters must be positive (zero allowed only for disabled options)")
    return values


def make_plan(limits=(1000.0,1500.0,2000.0), flex_spans=(0.0,50.0), battery_powers=(0.0,100.0)):
    if (not limits or not flex_spans or not battery_powers or
        any(not 0<v<=10000 for v in limits) or
        any(not 0<=v<=100 for v in flex_spans) or
        any(not 0<=v<=2000 for v in battery_powers)):
        raise ValueError("Unsupported hypothetical parameter ranges")
    combos=list(itertools.product(sorted(set(limits)),sorted(set(flex_spans)),sorted(set(battery_powers))))
    if len(combos)>64:raise ValueError("Sensitivity sweep limited to 64 optimizer calls")
    return combos


def run_sweep(
    input_path:Path, output:Path|None=None, *,
    limits=(1000.0,1500.0,2000.0), flex_spans=(0.0,50.0),
    battery_powers=(0.0,100.0), battery_hours=4.0,
) ->dict:
    if not (0<battery_hours<=24):
        raise ValueError("Hypothetical battery duration must be 0..24 h")
    plan=make_plan(limits,flex_spans,battery_powers)
    data=load_observed(input_path)
    baseline={}
    for limit in sorted(set(limits)):
        report,_=solve_case(data,"observed_reference",balancing_limit_mw=limit)
        baseline[limit]=report
    results=[]
    for limit,span,power in plan:
        name=("flat_100mw" if span==0 else "flexible_100mw")
        if power>0:name+="_with_battery"
        item,_=solve_case(
            data,name,balancing_limit_mw=limit,
            flex_span_mw=span,battery_power_mw=power if power>0 else 100.0,
            battery_hours=battery_hours
        )
        base=baseline[limit]
        result={
          "balancing_limit_mw_assumed":limit,
          "flex_half_range_mw_assumed":span,
          "battery_power_mw_assumed":power,
          "battery_energy_mwh_assumed":power*battery_hours,
          "model_scenario":name,
          "baseline_shortfall_mwh_under_same_assumed_limit":base["modelled_shortfall_under_assumption_mwh"],
          "added_load_energy_mwh":item["new_demand_mwh"],
          "shortfall_mwh_under_assumed_limit":item["modelled_shortfall_under_assumption_mwh"],
          "incremental_shortfall_vs_reference_mwh":round(item["modelled_shortfall_under_assumption_mwh"]-
            base["modelled_shortfall_under_assumption_mwh"],4),
          "balancing_supply_mwh_under_assumed_limit":item["assumed_balancing_support_mwh"],
          "battery_charge_mwh":item["battery_charge_mwh"],
          "battery_discharge_mwh":item["battery_discharge_mwh"],
          "solver_status":item["solver_status"],
          "solver_termination":item["termination"],
          "max_balance_error_mw":item["max_model_balance_error_mw"]
        }
        if item["solver_status"]!="ok" or item["termination"]!="optimal" or item["max_model_balance_error_mw"]>1e-5:
            raise AssertionError("Cannot release failed or unbalanced PyPSA sensitivity")
        if abs(item["new_demand_mwh"]-len(data)*0.25*100)>1e-5:
            raise AssertionError("Changed energy or time weighting in sensitivity grid")
        results.append(result)
    digest=hashlib.sha256(input_path.read_bytes()).hexdigest()
    payload={
      "study":"Fingrid national observed profile with hypothetical 100 MW project sensitivity",
      "model_version":MODEL_VERSION,
      "data_kind":"model_scenario",
      "input_utc":{"start":data["timestamp_utc"].iloc[0],"end":data["interval_end_utc"].iloc[-1]},
      "complete_observed_days":int(len(data)//96),
      "source_interval_count":int(len(data)),
      "observed_input_sha256":digest,
      "source_urls":["https://data.fingrid.fi/en/datasets/124","https://data.fingrid.fi/en/datasets/74"],
      "sweep_design":{
        "balancing_support_limits_mw_assumed":sorted(set(limits)),
        "flex_load_half_spans_mw_assumed":sorted(set(flex_spans)),
        "battery_powers_mw_assumed":sorted(set(battery_powers)),
        "battery_duration_hours_assumed":battery_hours,
        "battery_round_trip_efficiency_assumed":0.9,
        "new_load_nominal_mw":100.0,
        "solved_combinations":len(plan),
        "reference_solutions":len(baseline),
      },
      "baselines":[{
        "balancing_limit_mw_assumed":limit,
        "shortfall_mwh_under_assumed_limit":baseline[limit]["modelled_shortfall_under_assumption_mwh"],
        "balancing_supply_mwh_under_assumed_limit":baseline[limit]["assumed_balancing_support_mwh"]
      } for limit in sorted(baseline)],
      "results":results,
      "interpretation":"Optimization stress test only; no verified Finnish import capacity, national shortfall, grid connection feasibility, future forecast, or site-level result",
      "limitations":[
        "All modelled shortages are high-penalty slack beneath a USER-ASSUMED balancing limit, not actual outages.",
        "Fingrid 124/74 are historical national aggregate values, not time-resolved generator-level available capacity or actual interconnector rating.",
        "The selected dataset period is observational, not representative unless independently evaluated for seasonal or annual coverage.",
        "Flex range assumes daily energy neutrality but does not model ramp rate, service constraints, or business process.",
        "Battery cyclic state of charge and 90% round-trip efficiency are simplified hypothetical assumptions.",
        "No actual generation optimization, transmission network loadflow, grid-connectability study or price forecasting."
      ]
    }
    if output:
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print("PYPSA_SWEEP_SUMMARY_JSON="+json.dumps({
        k:v for k,v in payload.items() if k not in ("results","limitations")
    },sort_keys=True))
    return payload


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--limits",default="1000,1500,2000")
    p.add_argument("--flex-spans",default="0,50")
    p.add_argument("--battery-powers",default="0,100")
    p.add_argument("--battery-hours",type=float,default=4.0)
    a=p.parse_args(argv)
    run_sweep(a.input,a.output,
      limits=csv_list(a.limits),
      flex_spans=csv_list(a.flex_spans,allow_zero=True),
      battery_powers=csv_list(a.battery_powers,allow_zero=True),
      battery_hours=a.battery_hours)


if __name__=="__main__":
    main()
