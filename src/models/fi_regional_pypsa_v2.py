"""Finland v2: two-region electricity-supply stress OPF on real Fingrid observations.

Geography, north/south allocation, thermal interface capacities and flexible
site load are HYPOTHETICAL. Not a mapped Finnish 2025 network nor a site headroom
prediction. Outputs model sensitivity to assumed North/South cut constraints.

The 192 measured 2026 quarter-hours are source-hash and interval checked by
src.models.finland.load_observed; no generation-dispatch reconstruction is claimed.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import pandas as pd
from src.models.finland import load_observed, INPUT_PATH, additional_load

SCENARIOS=("reference","flat_100mw","flex_100mw","flat_100mw_derated_corridor")
ASSUMPTIONS={
 "north_load_fraction":.45,"north_observed_generation_fraction":.65,
 "north_south_line_impedance_r_ohm":.6,
 "north_south_line_impedance_x_ohm":5.0,
 "normal_regional_corridor_mva":1500.0,
 "derated_corridor_mva":750.0,
 "assumed_balancing_generator_north_mw":2000.0,
 "assumed_balancing_generator_south_mw":2000.0,
 "assumed_marginal_cost_index":1.0,
 "shortfall_relaxation_penalty_index":10000.0,
 "snapshot_weight_hours":.25,
}
VERSION="fi-two-region-hypothetical-v2"


def build(observed:pd.DataFrame, scenario:str):
 import pypsa
 if scenario not in SCENARIOS:raise ValueError("Unsupported scenario")
 n=pypsa.Network()
 n.set_snapshots(pd.DatetimeIndex(observed.index))
 n.snapshot_weightings.loc[:,:]=.25
 for bus in ("FI_north_PROXY","FI_south_PROXY"):n.add("Bus",bus,v_nom=400)
 corridor=ASSUMPTIONS["derated_corridor_mva"] if scenario=="flat_100mw_derated_corridor" else ASSUMPTIONS["normal_regional_corridor_mva"]
 n.add("Line","SYNTHETIC_NORTH_SOUTH_AC",bus0="FI_north_PROXY",bus1="FI_south_PROXY",
       r=ASSUMPTIONS["north_south_line_impedance_r_ohm"],
       x=ASSUMPTIONS["north_south_line_impedance_x_ohm"],b=0.,s_nom=corridor)
 generation=observed["production_mwh_per_hour"].astype(float)
 load=observed["consumption_mwh_per_hour"].astype(float)
 for region,frac_gen,frac_load in (
   ("FI_north_PROXY",ASSUMPTIONS["north_observed_generation_fraction"],ASSUMPTIONS["north_load_fraction"]),
   ("FI_south_PROXY",1-ASSUMPTIONS["north_observed_generation_fraction"],1-ASSUMPTIONS["north_load_fraction"])
 ):
  fixed=frac_gen*generation
  name=region+"_fixed_observed_generation_share"
  nameplate=float(fixed.max()+1)
  n.add("Generator",name,bus=region,p_nom=nameplate,marginal_cost=0)
  n.generators_t.p_min_pu[name]=fixed/nameplate
  n.generators_t.p_max_pu[name]=fixed/nameplate
  n.add("Load",region+"_hypothetically_allocated_national_load",
        bus=region,p_set=frac_load*load)
  n.add("Generator",region+"_hypothetical_balancing_supply",bus=region,p_nom=ASSUMPTIONS[
    "assumed_balancing_generator_north_mw" if region=="FI_north_PROXY" else "assumed_balancing_generator_south_mw"],
    marginal_cost=ASSUMPTIONS["assumed_marginal_cost_index"])
  n.add("Generator",region+"_model_unserved_relaxation_NOT_OUTAGE",bus=region,
        p_nom=float(load.max()+5000),marginal_cost=ASSUMPTIONS["shortfall_relaxation_penalty_index"])
  # Demand can be smaller than supply; allow a model-only surplus sink.
  n.add("Generator",region+"_model_surplus_sink_NOT_EXPORT",bus=region,
        p_nom=float(generation.max()+5000),p_min_pu=-1,p_max_pu=0,marginal_cost=-.01)
 if scenario!="reference":
  project=additional_load(observed,"flexible_100mw" if scenario=="flex_100mw" else "flat_100mw")
  n.add("Load","HYPOTHETICAL_SOUTHERN_100MW_DC",bus="FI_south_PROXY",p_set=project)
 return n


def solve(observed:pd.DataFrame,case:str)->dict:
 n=build(observed,case)
 status,termination=n.optimize(solver_name="highs",log_to_console=False)
 if status!="ok" or termination!="optimal":raise RuntimeError(f"Regional solver failed: {status}/{termination}")
 weights=.25
 flows=n.lines_t.p0["SYNTHETIC_NORTH_SOUTH_AC"].astype(float)
 rating=float(n.lines.at["SYNTHETIC_NORTH_SOUTH_AC","s_nom"])
 if (flows.abs()>rating+1e-3).any():raise AssertionError("Proxy corridor violated MVA-dispatch envelope")
 pairs={}
 for label in ("FI_north_PROXY","FI_south_PROXY"):
  pairs[label]={
   "assumed_balancing_mwh":round(float(n.generators_t.p[label+"_hypothetical_balancing_supply"].sum()*weights),4),
   "model_shortfall_mwh":round(float(n.generators_t.p[label+"_model_unserved_relaxation_NOT_OUTAGE"].sum()*weights),4)
  }
 return {
   "scenario":case,"solver_status":status,"termination":termination,
   "historical_intervals":len(observed),"source_window_hours":len(observed)*weights,
   "assumed_transmission_limit_mva":rating,
   "peak_assumed_corridor_transfer_mw":round(float(flows.abs().max()),5),
   "mean_assumed_corridor_flow_mw":round(float(flows.mean()),5),
   "intervals_at_or_near_assumed_limit":int((flows.abs()>=rating-1.).sum()),
   "regional":pairs,
   "total_model_shortfall_mwh":round(sum(x["model_shortfall_mwh"] for x in pairs.values()),4),
   "source_geographical_allocation_verified":False,
   "thermal_line_rating_operator_verified":False,
   "actual_Finnish_energy_unserved":False
 }


def run(input_path:Path=INPUT_PATH)->dict:
 data=load_observed(input_path)
 if len(data)!=192:raise ValueError("P1 prototype v2 only covers audited 48h complete pair")
 cases=[solve(data,name) for name in SCENARIOS]
 return {
  "model_version":VERSION,"status":"solved_two_region_assumption_stress_NOT_physical_network",
  "original_source_csv_sha256":hashlib.sha256(input_path.read_bytes()).hexdigest(),
  "input_kind":"real_observed_2026_Fingrid_124_74_15min_national_TOTALS",
  "source_interval_count":len(data),
  "assumptions":ASSUMPTIONS,"scenario_count":len(cases),"scenarios":cases,
  "operator_verified_location_specific_capacity_mw":None,
  "physical_2025_network_or_geography_verified":False,
  "geographic_weighting_assumption_warning":"Fixed invented north/south consumption and generation shares are NOT sourced region data; no real grid line rating is claimed.",
  "financial_or_blackout_predictions":False
 }


def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--observed",type=Path,default=INPUT_PATH)
 parser.add_argument("--out",type=Path,required=True)
 a=parser.parse_args(argv);r=run(a.observed)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
 print("FI_V2_REGIONAL="+json.dumps({
    "scenario_count":len(r["scenarios"]),
    "results":[{"scenario":x["scenario"],"slack_mwh":x["total_model_shortfall_mwh"],
                "line_transfer_mw":x["peak_assumed_corridor_transfer_mw"]} for x in r["scenarios"]],
    "operator_site_mw":None}))

if __name__=="__main__":main()
