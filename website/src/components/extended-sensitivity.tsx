"use client";
import {useMemo,useState} from "react";
import {BarChart,Bar,XAxis,YAxis,CartesianGrid,ResponsiveContainer,Tooltip} from "recharts";
type Entry={
 balancing_limit_mw_assumed:number;flex_half_range_mw_assumed:number;
 battery_power_mw_assumed:number;battery_energy_mwh_assumed:number;
 model_scenario:string;baseline_shortfall_mwh_under_same_assumed_limit:number;
 added_load_energy_mwh:number;shortfall_mwh_under_assumed_limit:number;
 incremental_shortfall_vs_reference_mwh:number;
 balancing_supply_mwh_under_assumed_limit:number;
 battery_charge_mwh:number;battery_discharge_mwh:number;
 solver_status:string;solver_termination:string;max_balance_error_mw:number;
};
type Study={
 complete_days:number;source_intervals:number;results:Entry[];
 limitations:string[];source_run:{workflow_url:string};
 model_assumptions:{balancing_ceiling_mw:number[];new_load_average_mw:number};
};
const fm=(n:number)=>n.toLocaleString("en-US",{maximumFractionDigits:1});
const key=(r:Entry)=>r.flex_half_range_mw_assumed===0?
   (r.battery_power_mw_assumed===0?"Continuous +100 MW":"Continuous + battery"):
   (r.battery_power_mw_assumed===0?"Flexible +100 MW":"Flexible + battery");
const allNames=["Continuous +100 MW","Continuous + battery","Flexible +100 MW","Flexible + battery"];
export function ExtendedSensitivity({data}:{data:Study}){
 const [ceiling,setCeiling]=useState(1500);
 const chart=useMemo(()=>data.results.filter(r=>r.balancing_limit_mw_assumed===ceiling)
  .sort((a,b)=>allNames.indexOf(key(a))-allNames.indexOf(key(b)))
  .map(r=>({name:key(r),shortfall:r.incremental_shortfall_vs_reference_mwh,actual:r.shortfall_mwh_under_assumed_limit})),
  [data,ceiling]);
 const reference=data.results.find(x=>x.balancing_limit_mw_assumed===ceiling)?.baseline_shortfall_mwh_under_same_assumed_limit;
 const full=(field:(r:Entry)=>number)=>data.model_assumptions.balancing_ceiling_mw.map(cap=>{
  const group=data.results.filter(r=>r.balancing_limit_mw_assumed===cap);
  return {cap,vals:allNames.map(n=>field(group.find(r=>key(r)===n)!))};
 });
 return <>
 <section className="lh-stats" aria-label="Historical study statistics">
  <div><small>OBSERVED SOURCE PERIOD</small><strong>{data.complete_days} days</strong><span>2025 September–October, not forecast</span></div>
  <div><small>VALIDATED SOURCE INTERVALS</small><strong>{fm(data.source_intervals)}</strong><span>Consumption and production paired by UTC</span></div>
  <div><small>MODEL SCENARIOS</small><strong>{data.results.length}</strong><span>Each solved optimally and balanced</span></div>
  <div><small>GROSS ADDED LOAD</small><strong>72,000 MWh</strong><span>Same total energy in every project case</span></div>
 </section>
 <section className="lh-panel">
  <div className="lh-section-top"><div><p className="lh-kicker">01 / PARAMETER SWEEP</p><h2>Compare explicit balancing assumptions</h2>
    <p>Switch between assumed balancing limits. The values below show <strong>incremental model shortfall</strong> above that limit's own reference (no added project).</p>
   </div><div className="lh-assumption"><label htmlFor="lh-cap">Hypothetical support cap</label><select id="lh-cap" value={ceiling} onChange={e=>setCeiling(Number(e.target.value))}>{data.model_assumptions.balancing_ceiling_mw.map(n=><option key={n} value={n}>{fm(n)} MW assumed</option>)}</select></div>
  </div>
  <div className="lh-report-line"><span>Reference model shortfall under {fm(ceiling)} MW assumed support</span><strong>{fm(reference??0)} MWh</strong></div>
  <div className="lh-graph" aria-label="Modelled additional shortfall energy under specified balancing assumption">
   <ResponsiveContainer width="100%" height="100%">
    <BarChart data={chart} margin={{top:8,right:18,left:14,bottom:26}}>
     <CartesianGrid stroke="#dce9f5" vertical={false}/>
     <XAxis dataKey="name" tick={{fontSize:10,fill:"#6c839b"}} interval={0} height={58}/>
     <YAxis tick={{fontSize:10,fill:"#6c839b"}} width={62}/>
     <Tooltip formatter={v=>[fm(Number(v))+" MWh","Incremental model shortfall"]}/>
     <Bar dataKey="shortfall" fill="#357bb1" radius={[5,5,0,0]} isAnimationActive={false}/>
    </BarChart>
   </ResponsiveContainer>
  </div>
  <div className="lh-cards">
   {chart.map(r=><article key={r.name}><small>{r.name}</small><strong>{fm(r.shortfall)} <em>MWh</em></strong><span>Additional penalty-slack energy relative to matching reference</span></article>)}
  </div>
  <p className="lh-chart-caution">Shortfall is a mathematical penalty variable caused by the imposed synthetic balancing limit, not actual customer interruption. Its absolute and incremental values have no directly validated relationship to Finnish import capacity or grid feasibility.</p>
 </section>
 <section className="lh-panel">
  <div className="lh-section-top"><div><p className="lh-kicker">02 / FULL FACTORIAL RESULTS</p><h2>Every assumption combination</h2><p>Each cell is the change in hypothetical model shortfall versus the reference with the same imposed balancing ceiling. Units are MWh over the 30-day historical sample.</p></div></div>
  <div className="lh-table-scroll"><table className="lh-matrix">
   <thead><tr><th>Hypothetical ceiling</th>{allNames.map(n=><th key={n}>{n}</th>)}</tr></thead>
   <tbody>{full(r=>r.incremental_shortfall_vs_reference_mwh).map(g=><tr key={g.cap}><th>{fm(g.cap)} MW</th>{g.vals.map((v,i)=><td key={i}>{fm(v)} MWh</td>)}</tr>)}</tbody>
  </table></div>
  <p className="lh-chart-caution">Flexibility is an optimistic hindsight schedule chosen from real observed residuals, not an actual demand response commitment. Storage and balancing quantities are scenario assumptions. No cost savings are estimated.</p>
 </section>
 <section className="lh-limitations"><h2>Research validity and next work</h2>{data.limitations.map((t,i)=><p key={i}>{t}</p>)}</section>
 </>;
}
