"use client";
import {useState} from "react";
import results from "@/lib/krios-engineering-verified-2026.json";

const difference=(a:number,b:number,n=2)=>(a>=b?"+":"")+(a-b).toFixed(n);
function Stat({title,value,detail}:{title:string;value:string;detail:string}){
 return <div className="research-card"><span className="kicker">{title}</span><h3>{value}</h3><p>{detail}</p></div>;
}
export function EngineeringScenarioExplorer(){
 const [hv,setHv]=useState(100);
 const [mv,setMv]=useState(2);
 const [regional,setRegional]=useState("flat_100mw_derated_corridor");
 const h=results.cigre_hv.cases.find(x=>x.added_mw===hv)??results.cigre_hv.cases[0];
 const h0=results.cigre_hv.cases[0];
 const m=results.cigre_mv.cases.find(x=>x.added_mw===mv)??results.cigre_mv.cases[0];
 const m0=results.cigre_mv.cases[0];
 const r=results.fingrid_regional_v2.scenarios.find(x=>x.name===regional)??results.fingrid_regional_v2.scenarios[0];
 const r0=results.fingrid_regional_v2.scenarios[0];
 return <div style={{display:"grid",gap:28}}>
 <section className="research-card">
  <span className="kicker">01 / Nonlinear AC + N−1 / standard 13-bus CIGRE high-voltage reference</span>
  <h3>Hypothetical data-centre connection</h3>
  <p>Actual pandapower 3.5.6 solver results. The additional load is connected at a chosen benchmark bus, at an assumed power factor of 0.95. These are not actual Fingrid station calculations.</p>
  <label>Additional load <select value={hv} onChange={e=>setHv(Number(e.target.value))}>
   {results.cigre_hv.cases.map(x=><option key={x.added_mw} value={x.added_mw}>{x.added_mw} MW</option>)}
  </select></label>
  <div className="grid-2" style={{marginTop:14}}>
   <Stat title="Minimum bus voltage" value={h.min_v_pu.toFixed(4)+" pu"} detail={difference(h.min_v_pu,h0.min_v_pu,4)+" pu vs original benchmark"}/>
   <Stat title="Peak line loading" value={h.max_line_loading_percent.toFixed(2)+"%"} detail={difference(h.max_line_loading_percent,h0.max_line_loading_percent)+" percentage points vs original"}/>
   <Stat title="Network losses" value={h.losses_mw.toFixed(2)+" MW"} detail={difference(h.losses_mw,h0.losses_mw)+" MW vs original"}/>
   <Stat title="N−1 unresolved outages" value={h.n1_nonconverged+" / "+h.n1_tested} detail={h.n1_converged_with_reference_violation+" converged outage cases also violated illustrative loading or voltage thresholds"}/>
  </div>
  <p className="footnote">One outage per physical reference line or transformer, 15 total. Non-converged studies are never treated as passes. A 0.9–1.1 pu flag is illustrative, not a Finnish grid code guarantee.</p>
 </section>
 <section className="research-card">
  <span className="kicker">02 / Medium-voltage feeder / standard 15-bus CIGRE benchmark</span>
  <h3>Realistic scale for feeder demonstration</h3>
  <p>Generic CIGRE MV network with wind/PV. Added loads stay within 0–2 MW—not an invented 100 MW MV grid connection in the Netherlands.</p>
  <label>Additional load <select value={mv} onChange={e=>setMv(Number(e.target.value))}>
   {results.cigre_mv.cases.map(x=><option key={x.added_mw} value={x.added_mw}>{x.added_mw} MW</option>)}
  </select></label>
  <div className="grid-2" style={{marginTop:14}}>
   <Stat title="Minimum voltage" value={m.min_v_pu.toFixed(4)+" pu"} detail="Converged CIGRE MV reference AC load flow"/>
   <Stat title="Maximum transformer loading" value={m.max_trafo_loading_percent.toFixed(2)+"%"} detail="CIGRE equipment nameplate percentage"/>
   <Stat title="Model feeder losses" value={m.losses_mw.toFixed(4)+" MW"} detail={difference(m.losses_mw,m0.losses_mw,4)+" MW vs reference"}/>
   <Stat title="Total model load" value={m.reference_total_load_mw.toFixed(2)+" MW"} detail="Existing generic feeder plus hypothetical project"/>
  </div>
 </section>
 <section className="research-card">
  <span className="kicker">03 / PyPSA v2 / real Fingrid timestamps, fictional geography</span>
  <h3>Regional transfer-assumption sensitivity</h3>
  <p>Two assumed Finnish regions, with 65% of recorded generation and 45% of recorded demand assigned north. The national source readings are authentic; the geographic shares and line ratings are invented inputs.</p>
  <label>Assumed scenario <select value={regional} onChange={e=>setRegional(e.target.value)}>
    {results.fingrid_regional_v2.scenarios.map(x=><option value={x.name} key={x.name}>{x.name.replaceAll("_"," ")}</option>)}
   </select></label>
  <div className="grid-2" style={{marginTop:14}}>
   <Stat title="Hypothetical corridor limit" value={r.line_cap_assumed_mva+" MVA"} detail="Not a Fingrid thermal limit or available grid headroom"/>
   <Stat title="Intervals near the model limit" value={r.near_cap_intervals+" / 192"} detail={difference(r.near_cap_intervals,r0.near_cap_intervals,0)+" intervals vs base assumption"}/>
   <Stat title="Hypothetical southern balancing" value={r.assumed_south_balancing_mwh.toFixed(1)+" MWh"} detail="Optimized assumption; not historical import or procurement"/>
   <Stat title="Model shortage relaxation" value={r.model_slack_mwh.toFixed(0)+" MWh"} detail="All four cases have fictional balancing resources; zero does not validate Finnish reliability"/>
  </div>
 </section>
 <section className="research-card">
  <span className="kicker">04 / AC verification / independent software stacks</span>
  <h3>pandapower versus PyPSA</h3>
  <p>Both packages independently solved the same explicitly specified artificial 110 kV, three-bus nonlinear AC network—not the CIGRE HV benchmark.</p>
  <div className="grid-2">
   <Stat title="Largest bus-voltage difference" value={results.identical_ac_crosssolver.maximum_voltage_difference_pu+" pu"} detail={"Predeclared tolerance "+results.identical_ac_crosssolver.tolerance_pu+" pu"}/>
   <Stat title="Largest line active-flow difference" value={results.identical_ac_crosssolver.maximum_active_branch_flow_difference_mw+" MW"} detail={"Predeclared tolerance "+results.identical_ac_crosssolver.tolerance_mw+" MW"}/>
  </div>
 </section>
 <section className="research-card">
  <span className="kicker">05 / ODbL Finnish source proxy / not 2025 calibration</span>
  <h3>Uncertainty in source-assigned line ratings</h3>
  <p>The following bars count 2024 OSM model records with hypothetical nominal rating below 1,500 MVA. These are NOT overloaded transmission lines or observed congestion.</p>
  <div style={{display:"grid",gap:12}}>
   {results.osm_input_uncertainty.assumed_rating_scale_cases.map(x=><div key={x.factor} style={{display:"grid",gridTemplateColumns:"70px 1fr 50px",alignItems:"center",gap:12}}>
    <span>{Math.round(x.factor*100)}%</span><div style={{height:10,background:"#8697a72b",overflow:"hidden",borderRadius:5}}>
     <div style={{height:"100%",width:(x.source_nominal_rating_under_1500_mva/137*100)+"%",background:"#6c9db9"}}/>
    </div><strong>{x.source_nominal_rating_under_1500_mva}</strong>
   </div>)}
  </div>
  <p>Across 137 source line records, {results.osm_input_uncertainty.graph_edge_disconnections} edge-removals disconnect the partial original graph. That is a topological observation, not operator N−1 compliance. Physical calibration remains blocked pending actual equipment, topology, spatial injection and measurement evidence.</p>
 </section>
 </div>;
}
