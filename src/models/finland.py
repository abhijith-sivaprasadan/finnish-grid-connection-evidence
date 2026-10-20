"""Single-bus Finland sensitivity, driven by *observed* aggregate Fingrid series.

NOT a validated Finnish transmission network, substation connection assessment,
generator dispatch reconstruction, or future forecast. Balancing exchange,
shortfall, surplus sink, flexibility and storage are explicitly hypothetical.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data/model_inputs/fingrid_20261015_20261016_15min.csv"
MODEL_VERSION = "pypsa-fi-single-bus-v1"
SCENARIOS = ("observed_reference", "flat_100mw", "flexible_100mw", "flat_100mw_with_battery")
ASSUMPTIONS = {
    "additional_load_mw": 100.0,
    "balancing_support_limit_mw": 1500.0,
    "hypothetical_flexible_min_mw": 50.0,
    "hypothetical_flexible_max_mw": 150.0,
    "battery_power_mw": 100.0,
    "battery_usable_energy_mwh": 400.0,
    "battery_round_trip_efficiency": 0.90,
    "snapshot_hours": 0.25,
    "shortfall_penalty_index_per_mwh": 10000.0,
    "surplus_absorption_penalty_index_per_mwh": 0.01,
    "balancing_cost_proxy": "dimensionless stress index (not a market price or currency)",
}


def load_observed(path: Path = INPUT_PATH) -> pd.DataFrame:
    data = pd.read_csv(path)
    expected = {
        "timestamp_utc", "interval_end_utc", "consumption_mwh_per_hour",
        "production_mwh_per_hour", "consumption_retrieved_at", "production_retrieved_at",
    }
    if set(data.columns) != expected or data.empty:
        raise ValueError("Expected only the fully attributed paired Fingrid input columns")
    starts = pd.to_datetime(data["timestamp_utc"], utc=True, errors="raise")
    ends = pd.to_datetime(data["interval_end_utc"], utc=True, errors="raise")
    if starts.isna().any() or ends.isna().any() or starts.duplicated().any():
        raise ValueError("UTC timestamps must be present and unique")
    if not starts.is_monotonic_increasing:
        raise ValueError("Rows must be ascending in UTC, without reordering source history")
    if len(starts) < 96 or len(starts) % 96:
        raise ValueError("Model input must contain complete 96-interval UTC days")
    delta = pd.Timedelta(minutes=15)
    if (ends - starts != delta).any() or (starts.diff().iloc[1:] != delta).any():
        raise ValueError("All paired source timestamps must be consecutive 15-minute UTC intervals")
    if not all((starts.dt.minute % 15 == 0) & (starts.dt.second == 0)):
        raise ValueError("Source timestamp must be aligned to a 15-minute boundary")
    if starts.iloc[0].hour != 0 or starts.iloc[0].minute != 0 or ends.iloc[-1].hour != 0 or ends.iloc[-1].minute != 0:
        raise ValueError("Only complete UTC days allowed")
    for column in ("consumption_mwh_per_hour", "production_mwh_per_hour"):
        values = pd.to_numeric(data[column], errors="raise")
        if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all() or (values < 0).any():
            raise ValueError(f"Invalid or nonphysical aggregate source number in {column}")
        data[column] = values.astype(float)
    for column in ("consumption_retrieved_at", "production_retrieved_at"):
        retrieved = pd.to_datetime(data[column], utc=True, errors="raise")
        if retrieved.isna().any() or (retrieved < ends).any():
            raise ValueError("Retrieval timestamp is missing or precedes the measured interval")
    data.index = starts.dt.tz_localize(None)
    return data


def additional_load(data: pd.DataFrame, scenario: str, *, flex_span_mw: float = 50.0) -> pd.Series:
    if scenario not in (*SCENARIOS, "flexible_100mw_with_battery"):
        raise ValueError(f"Unsupported scenario: {scenario}")
    if not np.isfinite(flex_span_mw) or not 0<=flex_span_mw<=100:
        raise ValueError("Hypothetical flexible-load half-span must be 0..100 MW")
    extra = pd.Series(0.0, index=data.index)
    if scenario == "observed_reference":
        return extra
    if not scenario.startswith("flexible_"):
        return pd.Series(100.0, index=data.index)
    residual = data["consumption_mwh_per_hour"] - data["production_mwh_per_hour"]
    # 48 lower-residual intervals per UTC day get 150 MW, other 48 get 50 MW.
    # 100 MW daily average and EXACTLY equal daily energy to the flat case.
    for _, positions in data.groupby(data.index.date).indices.items():
        positions = np.asarray(positions)
        if len(positions) != 96:
            raise ValueError("Incomplete day cannot support the daily energy-neutral flexibility rule")
        values = residual.iloc[positions].to_numpy()
        lowest = positions[np.argsort(values, kind="stable")[:48]]
        extra.iloc[positions] = 100.0-flex_span_mw
        extra.iloc[lowest] = 100.0+flex_span_mw
        if abs(float(extra.iloc[positions].sum()) - 9600.0) > 1e-8:
            raise AssertionError("Flexible demand failed equal daily energy constraint")
    return extra


def stress_cost_proxy(data: pd.DataFrame) -> pd.Series:
    residual = (data["consumption_mwh_per_hour"] - data["production_mwh_per_hour"]).clip(lower=0.0)
    scale = max(1.0, float(residual.quantile(0.95)))
    return 1.0 + residual / scale


def build_network(data: pd.DataFrame, scenario: str, *, balancing_limit_mw: float = 1500.0,
                  flex_span_mw: float = 50.0, battery_power_mw:float = 100.0,
                  battery_hours:float = 4.0):
    for k,v in {"balancing_limit_mw":balancing_limit_mw,"battery_power_mw":battery_power_mw,"battery_hours":battery_hours}.items():
        if not np.isfinite(v) or v<=0:
            raise ValueError(f"{k} must be finite and positive")
    try:
        import pypsa
    except ImportError as exc:
        raise RuntimeError("Install the optional pinned requirements-model.txt for PyPSA solving") from exc
    n = pypsa.Network()
    n.set_snapshots(pd.DatetimeIndex(data.index))
    n.snapshot_weightings.loc[:, :] = 0.25  # objective AND store energy: 15-minute intervals
    n.add("Bus", "FI_aggregate")
    generation = data["production_mwh_per_hour"].astype(float)
    consumption = data["consumption_mwh_per_hour"].astype(float)
    addition = additional_load(data, scenario,flex_span_mw=flex_span_mw)
    max_gen = float(generation.max()) + 1.0
    fraction = (generation / max_gen).rename("observed_generation")
    n.add("Generator", "observed_generation", bus="FI_aggregate", p_nom=max_gen,
          p_min_pu=fraction, p_max_pu=fraction, marginal_cost=0.0)
    n.add("Load", "observed_consumption", bus="FI_aggregate", p_set=consumption)
    n.add("Load", "assumed_new_load", bus="FI_aggregate", p_set=addition)
    n.add("Generator", "hypothetical_balancing_supply", bus="FI_aggregate", p_nom=balancing_limit_mw,
          marginal_cost=1.0)
    # This is a source-independent stress-weighted optimisation COST INDEX, not €
    n.generators_t.marginal_cost["hypothetical_balancing_supply"] = stress_cost_proxy(data)
    n.add("Generator", "model_unserved_relaxation", bus="FI_aggregate",
          p_nom=float(consumption.max()+2000),
          marginal_cost=10000.0)
    # Negative dispatch represents a hypothetical residual sink; it is not
    # a measured or operator-permitted cross-border export.
    n.add("Generator", "hypothetical_surplus_sink", bus="FI_aggregate",
          p_nom=float(generation.max()+1000),
          p_min_pu=-1.0, p_max_pu=0.0,
          marginal_cost=-0.01)
    if scenario.endswith("_with_battery"):
        n.add("StorageUnit", "hypothetical_battery", bus="FI_aggregate",
              p_nom=battery_power_mw, max_hours=battery_hours,
              efficiency_store=float(np.sqrt(0.90)),
              efficiency_dispatch=float(np.sqrt(0.90)),
              cyclic_state_of_charge=True, marginal_cost=0.01)
    return n


def solve_case(data: pd.DataFrame, scenario: str, *, balancing_limit_mw:float=1500.0,
               flex_span_mw:float=50.0, battery_power_mw:float=100.0,
               battery_hours:float=4.0) -> tuple[dict, list[dict]]:
    network = build_network(data,scenario,balancing_limit_mw=balancing_limit_mw,
                            flex_span_mw=flex_span_mw,battery_power_mw=battery_power_mw,
                            battery_hours=battery_hours)
    status, termination = network.optimize(solver_name="highs", log_to_console=False)
    if status != "ok" or termination != "optimal":
        raise RuntimeError(f"PyPSA/HiGHS did not yield an optimal solution for {scenario}")
    gen = network.generators_t.p
    support = gen["hypothetical_balancing_supply"].astype(float)
    shortfall = gen["model_unserved_relaxation"].astype(float)
    sink = gen["hypothetical_surplus_sink"].astype(float)
    observed_prod = gen["observed_generation"].astype(float)
    added = additional_load(data, scenario,flex_span_mw=flex_span_mw)
    obs_load = data["consumption_mwh_per_hour"].astype(float)
    if scenario.endswith("_with_battery"):
        unit = network.storage_units_t
        store = unit.p_store["hypothetical_battery"].astype(float)
        dispatch = unit.p_dispatch["hypothetical_battery"].astype(float)
    else:
        store = pd.Series(0.0, index=data.index)
        dispatch = pd.Series(0.0, index=data.index)
    balance = observed_prod + support + shortfall + sink + dispatch - store - obs_load - added
    max_error = float(balance.abs().max())
    max_generation_error = float((observed_prod - data["production_mwh_per_hour"]).abs().max())
    if max_error > 1e-5 or max_generation_error > 1e-5:
        raise AssertionError(f"Historical evidence / model balance failed: {max_error}, {max_generation_error}")
    cost = stress_cost_proxy(data)
    interval=0.25
    energy=lambda x: round(float(x.sum()*interval), 4)
    summary={
        "scenario":scenario, "solver_status":status,"termination":termination,
        "historical_interval_count":len(data),"window_hours":len(data)*interval,
        "observed_load_mwh":energy(obs_load),"observed_production_mwh":energy(observed_prod),
        "new_demand_mwh":energy(added),
        "assumed_balancing_support_mwh":energy(support),
        "modelled_shortfall_under_assumption_mwh":energy(shortfall),
        "assumed_surplus_disposal_mwh":energy(-sink),
        "battery_charge_mwh":energy(store),"battery_discharge_mwh":energy(dispatch),
        "max_balancing_support_mw":round(float(support.max()),4),
        "max_model_balance_error_mw":round(max_error,9),
        "proxy_dispatch_index_units":round(float(((support*cost)+(shortfall*10000)+(-sink*0.01)).sum()*interval),3)
    }
    if scenario!="observed_reference" and abs(summary["new_demand_mwh"]-100*len(data)*interval)>1e-6:
        raise AssertionError("Scenario changed total 100 MW equivalent demand energy")
    if (shortfall < -1e-6).any() or (support > balancing_limit_mw+1e-6).any():
        raise AssertionError("Dispatch crossed imposed hypothetical constraint")
    detail=[]
    for i,t in enumerate(data.index):
        detail.append({
           "timestamp_utc":t.isoformat()+"Z",
           "scenario":scenario,
           "source_consumption_mw":round(float(obs_load.iloc[i]),4),
           "source_production_mw":round(float(observed_prod.iloc[i]),4),
           "new_demand_mw":round(float(added.iloc[i]),4),
           "assumed_balancing_support_mw":round(float(support.iloc[i]),4),
           "modelled_shortfall_mw":round(float(shortfall.iloc[i]),4),
           "assumed_surplus_sink_mw":round(float(-sink.iloc[i]),4),
           "battery_charge_mw":round(float(store.iloc[i]),4),
           "battery_discharge_mw":round(float(dispatch.iloc[i]),4)
        })
    return summary,detail


def run(input_path: Path = INPUT_PATH, output:Path|None=None) -> dict:
    data=load_observed(input_path)
    summaries,details=[],[]
    for name in SCENARIOS:
        summary,records=solve_case(data,name)
        summaries.append(summary)
        details.extend(records)
    digest=hashlib.sha256(input_path.read_bytes()).hexdigest()
    payload={
      "model_version":MODEL_VERSION,
      "classification":"model_scenario",
      "verified_operator_connectability":False,
      "model_resolution":"one aggregate Finland bus; NO geographical or physical grid model",
      "source":"Fingrid Open Data actual Finnish national demand 124 and production 74, CC BY",
      "source_urls":["https://data.fingrid.fi/en/datasets/124","https://data.fingrid.fi/en/datasets/74"],
      "source_window_utc":{"start":data["timestamp_utc"].iloc[0],"end":data["interval_end_utc"].iloc[-1]},
      "observed_input_sha256":digest,
      "assumptions":ASSUMPTIONS,
      "limitations":[
       "This is a short historical 2026 sensitivity exercise, not a 2030 forecast or representative annual simulation.",
       "Observed Finland-wide generation is forced as a nondispatchable historical injection; no plant-level merit order or reserves are inferred.",
       "The 1500 MW balancing allowance is a HYPOTHETICAL scenario stress cap, NOT a measured interconnector capacity or import right.",
       "The balancing cost index is synthetic and dimensionless, NOT an observed market price or financial cost.",
       "Surplus is disposed through a hypothetical sink, not attributed to measured exports or curtailment.",
       "Shortfall means infeasibility within the chosen hypothetical bound, NOT real electricity shortages.",
       "Flexibility 50/150 MW and battery 100 MW / 400 MWh are hypothetical project capabilities; each case has equivalent gross new demand.",
       "Does not calculate local grid headroom at Seinäjoki, Uusnivala, or any other Fingrid point."
      ],
      "scenarios":summaries,
      "intervals":details
    }
    if output is not None:
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PYPSA_MODEL_SUMMARY_JSON="+json.dumps({k:v for k,v in payload.items() if k!="intervals"},sort_keys=True))
    return payload


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,default=INPUT_PATH)
    p.add_argument("--output",type=Path,default=ROOT/"data/model_outputs/finland_pypsa_20261015_16.json")
    args=p.parse_args(argv)
    run(args.input,args.output)


if __name__=="__main__":
    main()
