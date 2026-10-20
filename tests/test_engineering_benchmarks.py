"""Engineering reproducibility tests require the optional pinned modelling env."""
import pytest
from src.models.cigre_engineering_lab import run as cigre,add_project,HV_MW,MV_MW
from src.models.ac_cross_solver_reference import run as cross
from src.models.fi_regional_pypsa_v2 import run as regional
from src.models.finland import INPUT_PATH

def test_cigre_reference_source_two_distinct_scales():
 import pandapower.networks as pn
 import pandapower as pp
 n=pn.create_cigre_network_hv()
 assert len(n.bus)==13 and len(n.line)==9 and len(n.trafo)==6
 assert add_project(n,100,family="HV")["hypothetical_load_mw"]==100
 assert len(n.load)>5
 m=pn.create_cigre_network_mv(with_der="pv_wind")
 assert len(m.bus)==15 and len(m.line)==15
 assert add_project(m,2,family="MV")["hypothetical_load_mw"]==2
 with pytest.raises(ValueError):add_project(m,100,family="INVALID")

def test_cigre_solves_with_truthful_n1_outage_accounting():
 r=cigre()
 assert len(r["hv"])==len(HV_MW)==3 and len(r["mv"])==len(MV_MW)==4
 assert r["operator_approved_connection_mw"] is None
 assert r["real_fingrid_or_tennet_equipment"] is False
 assert r["hv"][0]["base"]["converged"] is True
 for case in r["hv"]:
  if case["n_minus_one"] is not None:
   x=case["n_minus_one"]
   assert x["tested_outages"]==15
   assert x["nonconverged"]+sum(s["converged"] for s in x["cases"])==15
 assert r["mv"][0]["base"]["converged"] is True

def test_three_bus_full_ac_crosssolver_reference():
 r=cross()
 assert r["benchmark_type"].startswith("DECLARED_SYNTHETIC")
 assert r["cross_solver_consistent_within_declared_tolerance"]
 assert r["max_bus_voltage_difference_pu"]<0.025
 assert r["max_line_from_bus_active_power_difference_mw"]<1.5

def test_regional_real_fingrid_48h_with_assumptions_only():
 r=regional(INPUT_PATH)
 assert r["source_interval_count"]==192
 assert r["scenario_count"]==4
 assert r["operator_verified_location_specific_capacity_mw"] is None
 assert r["physical_2025_network_or_geography_verified"] is False
 assert all(s["termination"]=="optimal" for s in r["scenarios"])
 assert all(s["total_model_shortfall_mwh"]>=0 for s in r["scenarios"])
 a={case["scenario"]:case for case in r["scenarios"]}
 assert a["flat_100mw_derated_corridor"]["assumed_transmission_limit_mva"]==750
 assert a["flat_100mw"]["assumed_transmission_limit_mva"]==1500
