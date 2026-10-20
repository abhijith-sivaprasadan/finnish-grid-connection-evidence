"""Reject hand-edited website model summaries inconsistent with actual solver artifacts.

Source files are the four separate output artifacts generated in the same
GitHub Actions engineering workflow. All comparisons retain explicit source
model scope; this checks INTERNAL publication integrity only.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import math
from src.db import ROOT

def assertion(a,b,label,abs_tol=1e-5):
    if isinstance(a, bool) or isinstance(b, bool):
        if a is not b: raise AssertionError(f"{label}: {a} != {b}")
    elif isinstance(a,(int,float)) and isinstance(b,(int,float)):
        if not math.isfinite(float(a)) or not math.isfinite(float(b)):
            raise AssertionError(f"{label}: nonfinite source or published value")
        if not math.isclose(float(a),float(b),abs_tol=abs_tol,rel_tol=0):
            raise AssertionError(f"{label}: {a} differs from original solver {b}")
    elif a!=b:raise AssertionError(f"{label}: {a!r} differs from original {b!r}")

def load(f):
    return json.loads(Path(f).read_text(encoding="utf8"))

def run(root=ROOT,*,cigre,regional,cross,osm):
    site=load(Path(root)/"website/src/lib/krios-engineering-verified-2026.json")
    hv=load(cigre); fi=load(regional);ac=load(cross); osm=load(osm)
    assert len(hv["hv"])==len(site["cigre_hv"]["cases"])==3
    assert len(hv["mv"])==len(site["cigre_mv"]["cases"])==4
    for index,(model,view) in enumerate(zip(hv["hv"],site["cigre_hv"]["cases"])):
        pre=f"cigre_hv[{index}]"
        assertion(view["added_mw"],model["site"]["hypothetical_load_mw"],pre+".added_mw")
        for left,right in (
            ("total_reference_load_mw","total_load_mw"),
            ("min_v_pu","min_v_pu"),("max_v_pu","max_v_pu"),
            ("max_line_loading_percent","max_line_loading_percent"),
            ("max_trafo_loading_percent","max_trafo_loading_percent"),
            ("losses_mw","network_losses_mw")):
            assertion(view[left],model["base"][right],pre+"."+left)
        for left,right in (("n1_tested","tested_outages"),("n1_nonconverged","nonconverged"),
                           ("n1_converged_with_reference_violation","converged_with_reference_violation")):
            assertion(view[left],model["n_minus_one"][right],pre+"."+left)
    for index,(model,view) in enumerate(zip(hv["mv"],site["cigre_mv"]["cases"])):
        pre=f"cigre_mv[{index}]"
        assertion(view["added_mw"],model["site"]["hypothetical_load_mw"],pre+".added_mw")
        for left,right in (("reference_total_load_mw","total_load_mw"),
                           ("min_v_pu","min_v_pu"),
                           ("max_trafo_loading_percent","max_trafo_loading_percent"),
                           ("losses_mw","network_losses_mw")):
            assertion(view[left],model["base"][right],pre+"."+left)
    assertion(len(fi["scenarios"]),len(site["fingrid_regional_v2"]["scenarios"]),"FI scenario count")
    assertion(site["fingrid_regional_v2"]["source_national_original_csv_sha256"],
              fi["original_source_csv_sha256"],"original Fingrid source digest")
    assertion(fi["physical_2025_network_or_geography_verified"],False,"FI geographic validity")
    if fi["model_version"]!="fi-two-region-hypothetical-v2":
        raise AssertionError("Unexpected Finland model version")
    mapping=(("name","scenario"),("line_cap_assumed_mva","assumed_transmission_limit_mva"),
             ("near_cap_intervals","intervals_at_or_near_assumed_limit"),
             ("max_flow_mw","peak_assumed_corridor_transfer_mw"),
             ("assumed_north_balancing_mwh",None),("assumed_south_balancing_mwh",None),
             ("model_slack_mwh","total_model_shortfall_mwh"))
    for ix,(view,source) in enumerate(zip(site["fingrid_regional_v2"]["scenarios"],fi["scenarios"])):
        for left,right in mapping:
            if right is None:
                bus="FI_north_PROXY" if "north" in left else "FI_south_PROXY"
                wanted=source["regional"][bus]["assumed_balancing_mwh"]
            else:wanted=source[right]
            assertion(view[left],wanted,f"FI scenario {ix}.{left}")
    if site["identical_ac_crosssolver"]["original_CIGRE_crossvalidated"] is not False:
        raise AssertionError("Synthetic 3-bus wrongly claimed CIGRE verification")
    assertion(site["identical_ac_crosssolver"]["maximum_voltage_difference_pu"],
              ac["max_abs_bus_voltage_pu_difference"],"Threebus bus voltage diff",abs_tol=1e-12)
    assertion(site["identical_ac_crosssolver"]["maximum_active_branch_flow_difference_mw"],
              ac["max_abs_line_from_bus_active_MW_difference"],"Threebus line MW diff",abs_tol=1e-12)
    assertion(site["identical_ac_crosssolver"]["passed"],ac["within_predeclared_tolerance"],"AC parity")
    assertion(site["osm_input_uncertainty"]["source_lines"],osm["source_line_count"],"OSM original lines")
    assertion(site["osm_input_uncertainty"]["source_ac_buses"],osm["source_ac_bus_count"],"OSM AC buses")
    assertion(site["osm_input_uncertainty"]["graph_edge_disconnections"],
              osm["source_single_edge_topological_disconnect_count"],"OSM graph bridge count")
    assert len(osm["scenarios"])==len(site["osm_input_uncertainty"]["assumed_rating_scale_cases"])==3
    for i,(view,source) in enumerate(zip(site["osm_input_uncertainty"]["assumed_rating_scale_cases"],osm["scenarios"])):
        assertion(view["factor"],source["assumed_template_rating_scale"],f"OSM case {i}.factor")
        for v in (500,1000,1500):
            assertion(view[f"source_nominal_rating_under_{v}_mva"],
                      source["source_nominal_MVA_below_test_thresholds"][str(v)],
                      f"OSM case {i} below {v} MVA")
    if site["osm_input_uncertainty"]["operator_calibrated"] is not False:
        raise AssertionError("OSM calibration claim differs from source")
    return {"status":"all_website_model_summary_fields_checked_against_independent_solver_outputs",
            "source_case_counts":{"hv":len(hv["hv"]),"mv":len(hv["mv"]),"regional":len(fi["scenarios"]),
                                  "osm":len(osm["scenarios"])},
            "cross_solver_source_differences_rounded_in_original_run":True,
            "operator_physical_network_verification":False}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    for arg in ("cigre","regional","cross","osm"):
        p.add_argument("--"+arg,type=Path,required=True)
    args=p.parse_args(argv)
    print(json.dumps(run(args.root,cigre=args.cigre,regional=args.regional,
                         cross=args.cross,osm=args.osm),sort_keys=True))

if __name__=="__main__":main()
