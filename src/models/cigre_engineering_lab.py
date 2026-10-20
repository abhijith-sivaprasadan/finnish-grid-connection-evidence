"""CIGRE benchmark AC validation laboratory (NOT a Finnish/Dutch grid).

Two intentionally different scales:
HV: hypothetical 50/100 MW data-centre connection + N-1 line/transformer outages.
MV: separately hypothetical 0.5/1/2 MW DER-rich feeder, never 100 MW.
Outputs measured numerical solver metrics plus failure/nonconvergence cases, not
fabricated point connection MW or a regulator's voltage limit.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path

HV_MW=(0.,50.,100.)
MV_MW=(0.,0.5,1.,2.)
POWER_FACTOR=0.95
DOC="https://pandapower.readthedocs.io/en/v3.5.6/networks/cigre.html"
VERSION="cigre-ac-v1"


def add_project(net, mw:float, *, family:str, pf:float=POWER_FACTOR):
    import pandapower as pp
    if not (0.8<=pf<=1) or mw<0 or not math.isfinite(mw):
        raise ValueError("Finite MW and 0.8<= power factor <=1 required")
    # Selection is explicit and stable across reruns; not a real network place.
    if family=="HV":
        target=int(net.bus.index[net.bus.vn_kv>=110][-1])
    elif family=="MV":
        target=int(net.bus.index[net.bus.vn_kv.between(10,35)][-1])
    else:
        raise ValueError("Unknown benchmark family")
    if mw:
        q=mw*math.tan(math.acos(pf))
        pp.create_load(net,bus=target,p_mw=mw,q_mvar=q,name=f"SYNTHETIC_{family}_{mw:g}MW")
    return {"bus_index":target,"bus_label":str(net.bus.at[target,"name"]),
            "nominal_voltage_kv":float(net.bus.at[target,"vn_kv"]),
            "hypothetical_load_mw":mw,"hypothetical_load_mvar":round(mw*math.tan(math.acos(pf)),6),
            "assumed_power_factor":pf}


def calculate(net):
    import pandapower as pp
    pp.runpp(net,algorithm="nr",init="auto",numba=False,check_connectivity=True,max_iteration=50)
    if not bool(net.converged):raise RuntimeError("Power flow did not converge")
    vm=net.res_bus.vm_pu
    if vm.isna().any() or not vm.apply(math.isfinite).all():
        raise ValueError("Missing/non-finite solved bus voltage")
    loading_lines=net.res_line.loading_percent.dropna()
    loading_trafos=net.res_trafo.loading_percent.dropna()
    if not all(math.isfinite(float(v)) for v in list(loading_lines)+list(loading_trafos)):
        raise ValueError("Missing/non-finite loading")
    return {
        "converged":True,"bus_count":len(net.bus),"line_count":len(net.line),
        "trafo_count":len(net.trafo),"min_v_pu":round(float(vm.min()),6),
        "max_v_pu":round(float(vm.max()),6),
        "max_line_loading_percent":round(float(loading_lines.max()) if len(loading_lines) else 0.,4),
        "max_trafo_loading_percent":round(float(loading_trafos.max()) if len(loading_trafos) else 0.,4),
        "total_load_mw":round(float(net.res_load.p_mw.sum()),4),
        "total_sgen_mw":round(float(net.res_sgen.p_mw.sum()),4) if len(net.sgen) else 0.,
        "network_losses_mw":round(float(net.res_line.pl_mw.sum()+net.res_trafo.pl_mw.sum()),6),
        "explicit_reference_voltage_band_violation":bool((vm<0.9).any() or (vm>1.1).any()),
        "loading_above_nameplate_100pct":bool((loading_lines>100).any() or (loading_trafos>100).any())
    }


def nminus1(net, *, families=("line","trafo")):
    """One actual reference-branch removal at a time: failure is not hidden."""
    outcomes=[]
    for family in families:
        for idx in list(net[family].index):
            label=str(net[family].at[idx,"name"])
            original=bool(net[family].at[idx,"in_service"])
            if not original: continue
            net[family].at[idx,"in_service"]=False
            try:
                result=calculate(net)
                outcome={"outage_type":family,"outage_index":int(idx),
                         "outage_name":label,"converged":True,
                         "min_v_pu":result["min_v_pu"],"max_v_pu":result["max_v_pu"],
                         "max_line_loading_percent":result["max_line_loading_percent"],
                         "max_trafo_loading_percent":result["max_trafo_loading_percent"],
                         "reference_voltage_band_violation":result["explicit_reference_voltage_band_violation"],
                         "reference_loading_over_100pct":result["loading_above_nameplate_100pct"]}
            except (ValueError, RuntimeError, Exception) as exc:
                # A disconnected or unsolvable scenario is counted explicitly,
                # never invented as a converged and compliant scenario.
                outcome={"outage_type":family,"outage_index":int(idx),
                         "outage_name":label,"converged":False,
                         "reason_type":type(exc).__name__}
            finally:
                net[family].at[idx,"in_service"]=original
            outcomes.append(outcome)
    return {"cases":outcomes,"tested_outages":len(outcomes),
            "nonconverged":sum(not x["converged"] for x in outcomes),
            "converged_with_reference_violation":sum(x["converged"] and
                (x["reference_voltage_band_violation"] or x["reference_loading_over_100pct"]) for x in outcomes)}


def run():
    import pandapower as pp
    import pandapower.networks as pn
    report={"model_version":VERSION,"benchmark_source":DOC,
        "status":"reference_benchmark_simulation_not_a_real_country_grid",
        "pandapower_version":pp.__version__,
        "operator_approved_connection_mw":None,
        "real_fingrid_or_tennet_equipment":False,
        "reference_voltage_band_pu":[0.9,1.1],
        "voltage_band_kind":"illustrative_metric_NOT_country_technical_compliance",
        "hv":[],"mv":[]}
    for mw in HV_MW:
        net=pn.create_cigre_network_hv()
        site=add_project(net,mw,family="HV")
        try:
            base=calculate(net)
            outages=nminus1(net)
            report["hv"].append({"site":site,"base":base,"n_minus_one":outages})
        except Exception as exc:
            report["hv"].append({"site":site,"base":{"converged":False,"reason_type":type(exc).__name__},
                                 "n_minus_one":None})
    for mw in MV_MW:
        net=pn.create_cigre_network_mv(with_der="pv_wind")
        site=add_project(net,mw,family="MV")
        try:
            report["mv"].append({"site":site,"base":calculate(net)})
        except Exception as exc:
            report["mv"].append({"site":site,"base":{"converged":False,"reason_type":type(exc).__name__}})
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args(argv)
    result=run()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("CIGRE_LAB_SUMMARY="+json.dumps({
        "hv":[{"mw":x["site"]["hypothetical_load_mw"],"converged":x["base"]["converged"],
                "n1_count":x["n_minus_one"]["tested_outages"] if x["n_minus_one"] else 0} for x in result["hv"]],
        "mv":[{"mw":x["site"]["hypothetical_load_mw"],"converged":x["base"]["converged"]} for x in result["mv"]],
        "operator_approved_mw":None}))

if __name__=="__main__":main()
