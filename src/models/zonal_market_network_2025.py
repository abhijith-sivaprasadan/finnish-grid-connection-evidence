"""Three-zone historical Swedish intraday MARKET-corridor PyPSA test.

This is a constrained 3-BUS MARKET-ACCESS GRAPH, not an AC/DC engineering
power-flow network, not published physical NTC, and not Finnish substation
connectability. Each original Fingrid 38/39 15-minute post-day-ahead remaining
capacity series bounds its respective SE1->FI or SE3->FI link independently.
Swedish supply behind each link is assumed available (not observed).
SE1-only / SE3-only are explicit outage/dependence sensitivity assumptions.

The paper trail is fail-closed: immutable captured original CSV checksums,
2880 timestamp-aligned native source rows, no gap fill, no 2025 annual claim.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np
import pandas as pd
from src.models.finland import load_observed,additional_load
from datetime import datetime,timezone

def canonical(value:str)->str:
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None:raise ValueError("Source timestamp requires UTC offset")
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

SOURCE_JOIN_SHA="659092a40ac298a256ba79cf6f7361f999ac9cfb8ed38e4dbcdb7cc4aee5097d"
ORIGINAL_NATIONAL_SHA="3093f704484848919d83feb6c133c2e2abf2299566d5bd02a109e01b7fdec2e0"
START="2025-09-15T00:00:00.000000Z"
END="2025-10-15T00:00:00.000000Z"
ORIGINAL_INTERVALS=2880
NATIVE_COLS=["timestamp_utc","commercial_export_FI_SE1_mw","commercial_export_FI_SE3_mw",
             "unused_intraday_import_SE1_FI_mw","unused_intraday_import_SE3_FI_mw",
             "unused_intraday_import_two_swedish_borders_mw"]
BORDERS={"SE1":"unused_intraday_import_SE1_FI_mw","SE3":"unused_intraday_import_SE3_FI_mw"}
CORRIDORS=("SE1+SE3","SE1_only","SE3_only")
FLEX_SPANS=(0.,50.)
STORAGE_HOURS=(0.,2.,4.,8.)


def load_pinned_sources(market_csv:Path,national_csv:Path):
    if hashlib.sha256(market_csv.read_bytes()).hexdigest()!=SOURCE_JOIN_SHA:
        raise ValueError("Swedish-border source CSV SHA-256 mismatch")
    if hashlib.sha256(national_csv.read_bytes()).hexdigest()!=ORIGINAL_NATIONAL_SHA:
        raise ValueError("National source CSV SHA-256 mismatch")
    with market_csv.open(encoding="utf-8",newline="") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=NATIVE_COLS:raise ValueError("Unsupported Fingrid market-source columns")
        source=list(reader)
    original=load_observed(national_csv)
    if len(source)!=ORIGINAL_INTERVALS or len(original)!=ORIGINAL_INTERVALS:
        raise ValueError("Fingrid selected 30-day source window must have 2880 complete pairs")
    caps={x:[] for x in BORDERS}
    flows={x:[] for x in BORDERS}
    for i,row in enumerate(source):
        dt=pd.Timestamp(original.index[i]).to_pydatetime()
        expected=dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        if canonical(row["timestamp_utc"])!=expected:
            raise ValueError(f"Original border and national timestamps disagree at {i}")
        if i and dt-pd.Timestamp(original.index[i-1]).to_pydatetime()!=pd.Timedelta(minutes=15):
            raise ValueError("Noncontinuous historical source interval")
        for label,column in BORDERS.items():
            val=float(row[column])
            if not math.isfinite(val) or val<0:raise ValueError("Invalid or negative actual unused market capacity")
            caps[label].append(val)
            flow=float(row["commercial_export_FI_"+label+"_mw"])
            if not math.isfinite(flow):raise ValueError("Invalid original signed commercial flow")
            flows[label].append(flow)
        if abs(float(row["unused_intraday_import_two_swedish_borders_mw"])-
               sum(caps[x][-1] for x in BORDERS))>1e-5:
            raise ValueError("Observed original two-border capacity aggregation inconsistent")
    if canonical(source[0]["timestamp_utc"])!=START or (
        pd.Timestamp(original.index[-1])+pd.Timedelta(minutes=15)
       ).strftime("%Y-%m-%dT%H:%M:%S.%fZ")!=END:
        raise ValueError("Selected original 2025 source start/end mismatch")
    return original,{x:pd.Series(v,index=original.index,dtype=float) for x,v in caps.items()},flows


def solve_zonal(original,caps:dict,*,corridor:str,flex_mw:float,battery_hours:float):
    import pypsa
    if corridor not in CORRIDORS or flex_mw not in FLEX_SPANS or battery_hours not in STORAGE_HOURS:
        raise ValueError("Scenario configuration not explicitly permitted")
    load=additional_load(original,"flexible_100mw" if flex_mw else "flat_100mw",flex_span_mw=flex_mw)
    network=pypsa.Network()
    network.set_snapshots(pd.DatetimeIndex(original.index))
    network.snapshot_weightings.loc[:,:]=0.25
    network.add("Bus","FI_abstract_project_market")
    for zone in BORDERS:
        network.add("Bus",zone+"_abstract_supply")
    network.add("Load","hypothetical_100MW_project",bus="FI_abstract_project_market",p_set=load)
    network.add("Generator","slack_not_actual_Finnish_outage",bus="FI_abstract_project_market",
                p_nom=300.,marginal_cost=10000.)
    for zone in BORDERS:
        active=(corridor=="SE1+SE3" or corridor==zone+"_only")
        cap=caps[zone] if active else caps[zone]*0.
        max_cap=max(1.,float(cap.max()))
        network.add("Generator",zone+"_assumed_market_supplier",
                    bus=zone+"_abstract_supply",p_nom=max_cap,marginal_cost=1.)
        link=zone+"_operator_intraday_MARKET_space_not_physical"
        network.add("Link",link,bus0=zone+"_abstract_supply",bus1="FI_abstract_project_market",
                    efficiency=1.,p_nom=max_cap,p_max_pu=0.,p_min_pu=0.)
        network.links_t.p_max_pu[link]=cap/max_cap
    if battery_hours:
        network.add("StorageUnit","hypothetical_FI_battery",bus="FI_abstract_project_market",
                    p_nom=100.,max_hours=battery_hours,cyclic_state_of_charge=True,
                    efficiency_store=float(np.sqrt(.9)),
                    efficiency_dispatch=float(np.sqrt(.9)),marginal_cost=0.01)
    status,termination=network.optimize(solver_name="highs",log_to_console=False)
    if status!="ok" or termination!="optimal":
        raise ValueError("Zonal market access optimization did not solve optimal")
    links=network.links_t.p0
    dispatch={}
    imports=pd.Series(0.,index=original.index)
    for zone in BORDERS:
        actual=links[zone+"_operator_intraday_MARKET_space_not_physical"].astype(float)
        permitted=caps[zone] if (corridor=="SE1+SE3" or corridor==zone+"_only") else caps[zone]*0.
        if (actual<-1e-5).any() or (actual-permitted>1e-5).any():
            raise AssertionError("Corridor-specific original source market cap violated")
        dispatch[zone]=actual
        imports=imports+actual
    penalty=network.generators_t.p["slack_not_actual_Finnish_outage"].astype(float)
    if battery_hours:
        charge=network.storage_units_t.p_store["hypothetical_FI_battery"].astype(float)
        discharge=network.storage_units_t.p_dispatch["hypothetical_FI_battery"].astype(float)
    else:
        charge=pd.Series(0.,index=original.index)
        discharge=pd.Series(0.,index=original.index)
    imbalance=float((imports+penalty+discharge-charge-load).abs().max())
    if imbalance>1e-5:raise AssertionError("FI abstract project balance mismatch")
    energy=lambda x:round(float(x.sum()*0.25),4)
    if abs(energy(load)-72000.)>1e-5:raise AssertionError("New project must equal nominal 100 MW times 720h")
    return {
        "corridors_allowed":corridor,
        "flex_half_span_mw_assumed":flex_mw,
        "battery_duration_hours_assumed":battery_hours,
        "modelled_assumed_import_via_SE1_mwh":energy(dispatch["SE1"]),
        "modelled_assumed_import_via_SE3_mwh":energy(dispatch["SE3"]),
        "original_conditional_capacity_SE1_mwh":energy(caps["SE1"]),
        "original_conditional_capacity_SE3_mwh":energy(caps["SE3"]),
        "modelled_project_relaxation_mwh":energy(penalty),
        "modelled_project_energy_mwh":energy(load),
        "max_fi_bus_balance_error_mw":imbalance,
        "solver_status":status,"solver_termination":termination
    }


def run(market_csv:Path,national_csv:Path,outdir:Path):
    original,caps,flows=load_pinned_sources(market_csv,national_csv)
    results=[]
    for corridor in CORRIDORS:
        for flex in FLEX_SPANS:
            for hours in STORAGE_HOURS:
                res=solve_zonal(original,caps,corridor=corridor,flex_mw=flex,battery_hours=hours)
                results.append(res)
                print("VERIFIED_ZONAL_CASE_JSON="+json.dumps({
                  "corridor":corridor,"flex_mw":flex,"battery_hours":hours,
                  "project_relaxation_mwh":res["modelled_project_relaxation_mwh"]},sort_keys=True))
    if len(results)!=24:raise AssertionError("Missing corridor sensitivities")
    for flex in FLEX_SPANS:
        for hours in STORAGE_HOURS:
            both=next(x for x in results if x["corridors_allowed"]=="SE1+SE3" and
                      x["flex_half_span_mw_assumed"]==flex and x["battery_duration_hours_assumed"]==hours)
            single=[x for x in results if x["corridors_allowed"]!="SE1+SE3" and
                    x["flex_half_span_mw_assumed"]==flex and x["battery_duration_hours_assumed"]==hours]
            if any(both["modelled_project_relaxation_mwh"]>x["modelled_project_relaxation_mwh"]+1e-3 for x in single):
                raise AssertionError("Removing source-available corridors improved conditional least-relaxation optimum")
    payload={
      "status":"verified_original_source_market_constrained_three_bus_pypsa",
      "model_type":"three-abstract-bidding-zones_two_time_varying_independently_capped_market_links",
      "not_real_ac_dc_physical_grid_flow":True,
      "operator_confirmed_project_import_rights":False,
      "operator_confirmed_FI_point_connectability":False,
      "source_period_utc":["2025-09-15T00:00:00Z","2025-10-15T00:00:00Z"],
      "historical_original_source_ids":[31,32,38,39,124,74],
      "source_sha256":{"border_joined":SOURCE_JOIN_SHA,"national_original":ORIGINAL_NATIONAL_SHA},
      "observed_original_source_rows":2880,
      "source_border_definition":"Fingrid 38 and 39 remaining 15-minute SE1/SE3 to FI intraday trading capacity AFTER day-ahead, not physical NTC or any new customer's rights",
      "buses":["SE1_abstract_supply","SE3_abstract_supply","FI_abstract_project_market"],
      "independent_market_limited_links":["SE1->FI","SE3->FI"],
      "source_market_capacity_summary_mw":{
        x:{"min":round(float(v.min()),4),"median":round(float(v.median()),4),
           "max":round(float(v.max()),4)} for x,v in caps.items()},
      "assumptions":["100 MW extra project mean load at abstract FI market node",
        "Swedish zonal generator supply behind observed market links assumed always available up to published unused intraday trading capacity; NOT externally demonstrated",
        "Independent SE1 and SE3 links assumed lossless and unconstrained by internal Swedish or Finnish topology",
        "Source-derived 15-minute per-corridor market capacity; hypothetical corridor access with or without each border",
        "Marginal supply 1 artificial cost-unit/MWh and penalty 10,000 artificial cost-unit/MWh, not historical prices",
        "Battery 100 MW with 0/2/4/8h duration, 90% round-trip efficiency, cyclic SOC",
        "Flex scheduling uses historical hindsight, not real-world forecast information"],
      "cases":results,
      "limitations":[
        "This is a MARKET-CONSTRAINED 3-bus zonal GRAPH, not a Finnish AC/DC branch network or real DC OPF.",
        "Intraday unused import after day-ahead is neither physical line thermal capacity, secure deliverable power, nor legal import rights.",
        "The measured FI-SE1/SE3 commercial flows are not actual physical power measured on AC/DC circuits. They are used for context only.",
        "No internal Finnish line impedance, susceptance, P1 cut, substation topology or N-1 security model is present.",
        "A genuine Finnish spatially resolved physical network model needs documented grid buses, lines, impedances, thermal ratings, security limits and site location; absent data must not be guessed.",
        "Zonal generator availability is assumed, not sourced. 'Unserved' penalty is solver relaxation, NOT Finnish outages.",
        "Modelled SE1/SE3 dispatch split is arbitrary in equal-cost cases and NOT observed cross-border dispatch.",
        "Not a forecast, 2030 estimate, annual 2025 energy balance or connection-feasibility judgement."
      ]
    }
    outdir.mkdir(parents=True,exist_ok=True)
    (outdir/"verified_zonal_market_topology_2025.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print("ZONAL_MARKET_MODEL_SUMMARY_JSON="+json.dumps({
      "solved":len(results),
      "source_rows":2880,
      "site_capacity_confirmed":False,
      "network_type":"source_market_constrained_three_bus_not_physical_grid"
    },sort_keys=True))
    return payload


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--border-joined",required=True,type=Path)
    p.add_argument("--national-30days",required=True,type=Path)
    p.add_argument("--outdir",required=True,type=Path)
    a=p.parse_args(argv)
    run(a.border_joined,a.national_30days,a.outdir)


if __name__=="__main__":
    main()
