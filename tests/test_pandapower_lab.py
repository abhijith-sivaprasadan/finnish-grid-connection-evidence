"""CIGRE actual reference cases in pinned pandapower 3.5.6 environment."""
import pytest
from src.models.cigre_engineering_lab import run,add_project,HV_MW,MV_MW

def test_network_inventory_and_scale():
 import pandapower.networks as pn
 hv=pn.create_cigre_network_hv()
 assert (len(hv.bus),len(hv.line),len(hv.trafo))==(13,9,6)
 assert add_project(hv,100,family="HV")["hypothetical_load_mw"]==100
 mv=pn.create_cigre_network_mv(with_der="pv_wind")
 assert (len(mv.bus),len(mv.line))==(15,15)
 assert add_project(mv,2,family="MV")["hypothetical_load_mw"]==2
 with pytest.raises(ValueError):add_project(mv,100,family="UNKNOWN")

def test_source_benchmarks_have_truthful_case_coverage():
 r=run()
 assert len(r["hv"])==len(HV_MW)==3
 assert len(r["mv"])==len(MV_MW)==4
 assert r["real_fingrid_or_tennet_equipment"] is False
 assert r["operator_approved_connection_mw"] is None
 assert r["hv"][0]["base"]["converged"]
 assert r["mv"][0]["base"]["converged"]
 for case in r["hv"]:
  if case["n_minus_one"]:
   o=case["n_minus_one"]
   assert o["tested_outages"]==15
   assert sum(x["converged"] for x in o["cases"])+o["nonconverged"]==15

def test_synthetic_ac_benchmark_solver_is_finite():
 from src.models.ac_cross_solver_reference import pandapower_case
 s=pandapower_case()
 assert len(s["bus_v_pu"])==3
 assert len(s["line_from_p_mw"])==3
 assert all(.8<x<1.2 for x in s["bus_v_pu"].values())
