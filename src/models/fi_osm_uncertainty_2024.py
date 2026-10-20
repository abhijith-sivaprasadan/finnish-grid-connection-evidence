"""2024 OSM source branch-rating template uncertainty — NOT a calibrated 2025 grid.

Original 5 Zenodo source files and hashes are independently checked before
any derived ODbL result. This screens how many *nominal model assignments*
are below selected test-scale MVA thresholds under ±25% template scaling.
It DOES NOT compute power flow, line overload or predict real bottlenecks.
A calibration is BLOCKED until 2025 operator state, nodal injections, actual
branch limits and measurements (e.g. source-qualified P1 cut) exist.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from src.models.fi_proxy_n1_audit import verify_archive, electrical_template_audit, n1_structural_audit

FACTORS=(.75,1.,1.25)
TEST_LEVELS=(500.,1000.,1500.)

def run(root:Path)->dict:
 orig,tables=verify_archive(root)
 template=electrical_template_audit(tables["lines"])
 if not template["all_137_source_lines_fit_voltage_templates"]:raise ValueError("Unrecognized source engineering templates")
 topology=n1_structural_audit(tables)
 ratings=[float(row["s_nom"]) for row in tables["lines"]]
 if len(ratings)!=137 or any(not math.isfinite(x) or x<=0 for x in ratings):
  raise ValueError("Original source line rating missing/invalid")
 scenarios=[]
 for factor in FACTORS:
  vals=[x*factor for x in ratings]
  scenarios.append({
   "assumed_template_rating_scale":factor,
   "source_line_records":len(vals),
   "source_nominal_MVA_below_test_thresholds":{
       str(int(level)):sum(x<level for x in vals) for level in TEST_LEVELS},
   "source_rating_min_MVA":round(min(vals),3),
   "source_rating_max_MVA":round(max(vals),3),
   "not_observed_congestion":True
  })
 return {
  "scope":"licensed_ODbL_2024_OSM_proxy_template_uncertainty_NO_PF",
  "source_record":"https://doi.org/10.5281/zenodo.14144752",
  "source_license":"ODbL-1.0 adapted OSM and Xiong et al, attribution and share-alike",
  "source_edition":"v0.6; 2024 source collection",
  "verified_original_source_sha256":{key:x["sha256"] for key,x in orig["original_source_verified"].items()},
  "scenarios":scenarios,
  "source_ac_bus_count":topology["ac_bus_count"],
  "source_line_count":topology["ac_line_count"],
  "source_single_edge_topological_disconnect_count":topology["single_edge_removals_causing_graph_disconnection"],
  "study_year_2025_fingrid_operational_grid_verified":False,
  "individual_operator_branch_rating_verified_count":0,
  "operator_site_connection_headroom_mw":None,
  "actual_physical_grid_calibration_performed":False,
  "calibration_status":"BLOCKED_NOT_ENOUGH_OPERATOR_EQUIPMENT_AND_SPATIAL_INJECTION_EVIDENCE",
  "what_is_missing":["operator-confirmed 2025 branch IDs/energisation and line ratings",
                     "source-matched 110 kV and transformers, controlled switching",
                     "dated spatial generation and load allocation",
                     "comparable operator measured internal P1 flow/physical limit",
                     "N-1 operational boundary conditions and source-faithful contingencies"]
 }

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--extracted-dir",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args(argv)
 result=run(a.extracted_dir)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print("FI_OSM_RATING_SENSITIVITY="+json.dumps({
 "source_lines":result["source_line_count"],
 "scale_cases":len(result["scenarios"]),
 "2025_grid_calibration":False,
 "operator_approved_mw":None
 }))

if __name__=="__main__":main()
