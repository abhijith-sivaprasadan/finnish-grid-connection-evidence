"""Cross-package AC benchmark on IDENTICAL explicit 110-kV 3-bus network.

This is an artificial, parameter-specified reference with identical R/X,
slack, PQ and bus voltages. It is not claimed to be CIGRE or Finnish topology.
Comparing nonlinear AC results is more honest than equating PyPSA DC OPF and
pandapower AC PF. Any numerical differences are exported and tested.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path

LINES=[
 {"id":"A-B","from":"A","to":"B","length_km":10.0,"r_ohm_per_km":0.08,"x_ohm_per_km":0.30},
 {"id":"B-C","from":"B","to":"C","length_km":8.0,"r_ohm_per_km":0.08,"x_ohm_per_km":0.30},
 {"id":"A-C","from":"A","to":"C","length_km":16.0,"r_ohm_per_km":0.08,"x_ohm_per_km":0.30}
]
BUS_PQ={"A":(0.,0.),"B":(30.,10.),"C":(15.,5.)}
V_KV=110.
MAX_VOLT_DIFF_PU=0.025
MAX_BRANCH_P_DIFF_MW=1.5

def pandapower_case():
 import pandapower as pp
 grid=pp.create_empty_network(sn_mva=100.)
 idx={name:pp.create_bus(grid,vn_kv=V_KV,name=name) for name in BUS_PQ}
 pp.create_ext_grid(grid,idx["A"],vm_pu=1.,va_degree=0.)
 for bus,(p,q) in BUS_PQ.items():
  if p:pp.create_load(grid,idx[bus],p_mw=p,q_mvar=q)
 for line in LINES:
  pp.create_line_from_parameters(grid,idx[line["from"]],idx[line["to"]],
    length_km=line["length_km"],r_ohm_per_km=line["r_ohm_per_km"],
    x_ohm_per_km=line["x_ohm_per_km"],c_nf_per_km=0.,
    max_i_ka=2.,name=line["id"])
 pp.runpp(grid,algorithm="nr",numba=False,calculate_voltage_angles=True,init="flat")
 if not grid.converged:raise RuntimeError("pandapower reference did not converge")
 return {"bus_v_pu":{name:float(grid.res_bus.at[i,"vm_pu"]) for name,i in idx.items()},
         "line_from_p_mw":{line["id"]:float(grid.res_line.at[i,"p_from_mw"]) for i,line in enumerate(LINES)},
         "slack_p_mw":float(grid.res_ext_grid.p_mw.iloc[0]),
         "source":"pandapower nonlinear balanced AC Newton-Raphson"}

def pypsa_case():
 import pypsa
 import pandas as pd
 n=pypsa.Network()
 n.set_snapshots(pd.DatetimeIndex(["2026-10-20T00:00:00Z"]))
 for bus in BUS_PQ:n.add("Bus",bus,v_nom=V_KV)
 n.add("Generator","reference_slack",bus="A",control="Slack",p_nom=500.,p_set=0.)
 for bus,(p,q) in BUS_PQ.items():
  if p:n.add("Load","load_"+bus,bus=bus,p_set=p,q_set=q)
 for line in LINES:
  n.add("Line",line["id"],bus0=line["from"],bus1=line["to"],
        r=line["length_km"]*line["r_ohm_per_km"],
        x=line["length_km"]*line["x_ohm_per_km"],b=0.,s_nom=400.)
 n.pf()
 bus_v=n.buses_t.v_mag_pu.iloc[0]
 flows=n.lines_t.p0.iloc[0]
 values=[float(x) for x in list(bus_v)+list(flows)]
 if any(not math.isfinite(x) for x in values):raise RuntimeError("PyPSA AC results not finite")
 return {"bus_v_pu":{name:float(bus_v.loc[name]) for name in BUS_PQ},
         "line_from_p_mw":{line["id"]:float(flows.loc[line["id"]]) for line in LINES},
         "source":"PyPSA nonlinear full AC Newton-Raphson pf; not linear OPF"}

def run():
 a,b=pandapower_case(),pypsa_case()
 volts={name:round(abs(a["bus_v_pu"][name]-b["bus_v_pu"][name]),8) for name in BUS_PQ}
 mw={x["id"]:round(abs(a["line_from_p_mw"][x["id"]]-b["line_from_p_mw"][x["id"]]),6) for x in LINES}
 return {"status":"synthetic_same_parameter_AC_PF_cross_verification",
   "benchmark_type":"DECLARED_SYNTHETIC_3_BUS_NOT_CIGRE_OR_REAL_OPERATOR_NETWORK",
   "source_parameters":{"buses":BUS_PQ,"lines":LINES,"voltage_kv":V_KV,
       "reactive_power_mvar_explicit":True,"line_b_siemens":0.0},
   "pandapower":a,"pypsa":b,
   "max_bus_voltage_difference_pu":max(volts.values()),
   "max_line_from_bus_active_power_difference_mw":max(mw.values()),
   "per_bus_voltage_abs_difference_pu":volts,
   "per_line_active_flow_abs_difference_mw":mw,
   "validation_tolerances":{"voltage_pu":MAX_VOLT_DIFF_PU,"line_p_mw":MAX_BRANCH_P_DIFF_MW},
   "cross_solver_consistent_within_declared_tolerance":
       max(volts.values())<=MAX_VOLT_DIFF_PU and max(mw.values())<=MAX_BRANCH_P_DIFF_MW,
   "verified_Finnish_or_Dutch_network":False}

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--out",type=Path,required=True)
 args=p.parse_args(argv)
 result=run()
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print("CROSS_AC_PF="+json.dumps({"voltage_diff":result["max_bus_voltage_difference_pu"],
                               "flow_diff":result["max_line_from_bus_active_power_difference_mw"],
                               "within_tolerance":result["cross_solver_consistent_within_declared_tolerance"]}))
 if not result["cross_solver_consistent_within_declared_tolerance"]:
  raise RuntimeError("Do not publish cross-solver agreement: discrepant physical AC results")

if __name__=="__main__":main()
