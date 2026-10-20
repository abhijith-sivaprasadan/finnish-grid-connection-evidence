"""Dependency-free validation of separately solved full AC pandapower/PyPSA results."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path

def compare(p:dict,q:dict):
 if p["solver"]!="pandapower" or q["solver"]!="pypsa":
  raise ValueError("Results must originate from independently solved named AC engines")
 if p["reference"]!=q["reference"] or p["source_parameters"]!=q["source_parameters"]:
  raise ValueError("Not the identical parameterized benchmark")
 a=p["actual_full_AC_PF"];b=q["actual_full_AC_PF"]
 for field in ("bus_v_pu","line_from_p_mw"):
  if set(a[field])!=set(b[field]):raise ValueError("Missing comparable buses/lines")
 gaps={x:round(abs(float(a["bus_v_pu"][x])-float(b["bus_v_pu"][x])),8) for x in a["bus_v_pu"]}
 powers={x:round(abs(float(a["line_from_p_mw"][x])-float(b["line_from_p_mw"][x])),6) for x in a["line_from_p_mw"]}
 if not all(math.isfinite(x) for x in list(gaps.values())+list(powers.values())):
  raise ValueError("Nonfinite intersolver result")
 result={
  "status":"two_independent_full_AC_numerical_cross_validation",
  "model":"explicit_110kV_artificial_three_bus_NOT_CIGRE_OR_OPERATOR",
  "max_abs_bus_voltage_pu_difference":max(gaps.values()),
  "max_abs_line_from_bus_active_MW_difference":max(powers.values()),
  "voltage_tolerance_pu":.025,
  "flow_tolerance_mw":1.5,
  "bus_differences_pu":gaps,
  "line_differences_mw":powers,
  "within_predeclared_tolerance":max(gaps.values())<=.025 and max(powers.values())<=1.5,
  "not_fingrid_tennet_or_cigre_equipment_validation":True,
 }
 return result

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--pandapower",type=Path,required=True)
 p.add_argument("--pypsa",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args(argv)
 result=compare(json.loads(a.pandapower.read_text()),json.loads(a.pypsa.read_text()))
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print("CROSS_SOLVER_AC_VALIDATION="+json.dumps(result))
 if not result["within_predeclared_tolerance"]:
  raise RuntimeError("Independent AC packages disagree outside predeclared tolerances; no verified claim")

if __name__=="__main__":main()
