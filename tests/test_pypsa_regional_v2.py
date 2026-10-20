"""Run independently in pandas 3 / PyPSA 1.4 with source-pinned 2026 observations."""
from src.models.ac_cross_solver_reference import pypsa_case
from src.models.fi_regional_pypsa_v2 import run
from src.models.finland import INPUT_PATH

def test_pypsa_nonlin_full_ac_reference():
 s=pypsa_case()
 assert len(s["bus_v_pu"])==3
 assert len(s["line_from_p_mw"])==3
 assert all(.8<x<1.2 for x in s["bus_v_pu"].values())

def test_real_source_is_not_invented_spatial_history():
 data=run(INPUT_PATH)
 assert data["scenario_count"]==4
 assert data["source_interval_count"]==192
 assert data["operator_verified_location_specific_capacity_mw"] is None
 assert data["physical_2025_network_or_geography_verified"] is False
 assert all(s["termination"]=="optimal" for s in data["scenarios"])
