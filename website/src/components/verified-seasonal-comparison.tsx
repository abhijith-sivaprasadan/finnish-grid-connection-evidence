"use client";
import {useState} from "react";
import {ResponsiveContainer,BarChart,Bar,XAxis,YAxis,CartesianGrid,Tooltip,Legend} from "recharts";
type Season="winter"|"summer"|"autumn";
type RecordRow={balancing_limit_mw:number;flex_half_span_mw:number;battery_power_mw:number;incremental_penalty_shortfall_mwh:Record<Season,number>};
type Study={
 modelled_days_per_season:number;source_pairs_per_season:number;
 annual_2025_verified_complete:boolean;scenario_results:RecordRow[];
 model_windows:{season:string;start_utc:string;end_utc:string;sha256:string}[];
 original_30day_audit:Record<Season,{complete_days:number;total_days:number;missing_consumption_intervals:number;missing_production_intervals:number;missing_utc:string[]}>;
 assumptions:{new_demand_energy_mwh_per_season:number};
 limitations:string[];
 source_validation_run:string;
};
const seasons:Season[]=["winter","summer","autumn"];
const labels:Record<Season,string>={winter:"Winter",summer:"Summer",autumn:"Autumn"};
const names=(flex:number,battery:number)=>(flex>0?"Flexible":"Continuous")+(battery>0?" + battery":"");
const num=(n:number)=>n.toLocaleString("en-US",{maximumFractionDigits:1});
const cases=[{flex:0,battery:0},{flex:0,battery:100},{flex:50,battery:0},{flex:50,battery:100}];

export function VerifiedSeasonalComparison({study}:{study:Study}){
 const [cap,setCap]=useState(1500);
 const rows=cases.map(item=>{
   const match=study.scenario_results.find(x=>x.balancing_limit_mw===cap&&x.flex_half_span_mw===item.flex&&x.battery_power_mw===item.battery);
   if(!match)throw new Error("Scenario matrix incomplete");
   return {case:names(item.flex,item.battery),...match.incremental_penalty_shortfall_mwh};
 });
 const [selected,setSelected]=useState(0);
 const chart=seasons.map(s=>({season:labels[s],incremental:rows[selected][s]}));
 return <>
 <section className="vse-overview">
  <div><small>SOURCE COVERAGE</small><strong>3 × {study.modelled_days_per_season} days</strong><span>Selected continuous windows, not 90 days modelled</span></div>
  <div><small>REAL SOURCE PAIRS</small><strong>{num(study.source_pairs_per_season)} <em>per season</em></strong><span>Each pair is a native Fingrid 15-minute reading</span></div>
  <div><small>ASSUMED NEW LOAD</small><strong>{num(study.assumptions.new_demand_energy_mwh_per_season)} MWh</strong><span>Equal project energy in every season's model</span></div>
  <div><small>FULL-YEAR COMPLETENESS</small><strong>Not verified</strong><span>Never annualized from incomplete data</span></div>
 </section>
 <section className="vse-panel">
  <div className="vse-panel-head"><div><p className="vse-kicker">01 / HISTORICAL SOURCE COVERAGE</p><h2>Exact model windows</h2><p>Each period was selected from the longest uninterrupted run of source-complete days in its predeclared 30-day seasonal audit. The initial run capped all comparisons at fourteen days.</p></div></div>
  <div className="vse-table-overflow"><table className="vse-table">
   <thead><tr><th>Window</th><th>Selected UTC dates</th><th>Complete days in original source audit</th><th>Missing source readings</th></tr></thead>
   <tbody>{study.model_windows.map(w=>{
    const s=w.season as Season,coverage=study.original_30day_audit[s];
    return <tr key={s}><th>{labels[s]}</th><td>{w.start_utc.slice(0,10)} to {new Date(Date.parse(w.end_utc)-86400000).toISOString().slice(0,10)} (inclusive)</td><td>{coverage.complete_days}/{coverage.total_days}</td><td>{coverage.missing_consumption_intervals} consumption; {coverage.missing_production_intervals} production</td></tr>;
   })}</tbody></table></div>
  <p className="vse-note">Winter and summer source gaps are outside the selected model windows. This is not a claim of source completeness for either full 30-day period, nor proof that the entire 2025 calendar is complete.</p>
 </section>
 <section className="vse-panel">
  <div className="vse-panel-head"><div><p className="vse-kicker">02 / SOURCE-QUALIFIED SENSITIVITY</p><h2>Same project energy, different historical contexts</h2><p>Values are <strong>incremental hypothetical model penalty slack</strong> above the no-project reference at the selected assumed ceiling. Negative values can occur when hypothetical storage reduces model slack below the no-project baseline.</p></div>
   <label className="vse-cap">Assumed support ceiling<select value={cap} onChange={e=>{setCap(Number(e.target.value));setSelected(0);}}><option value={1000}>1,000 MW · assumption</option><option value={1500}>1,500 MW · assumption</option><option value={2000}>2,000 MW · assumption</option></select></label>
  </div>
  <div className="vse-tabbar" role="group" aria-label="Select model assumptions">{rows.map((r,i)=><button key={r.case} type="button" className={selected===i?"active":""} aria-pressed={selected===i} onClick={()=>setSelected(i)}>{r.case}</button>)}</div>
  <div className="vse-graph" aria-label="Incremental modelled penalty slack comparison for historical seasons">
   <ResponsiveContainer width="100%" height="100%">
    <BarChart data={chart} margin={{top:8,right:20,bottom:17,left:17}}>
     <CartesianGrid stroke="#e0eaf3" vertical={false}/>
     <XAxis dataKey="season" tick={{fontSize:11,fill:"#6785a1"}}/>
     <YAxis tick={{fontSize:10,fill:"#6785a1"}} width={70}/>
     <Tooltip formatter={v=>[num(Number(v))+" MWh","Incremental model penalty slack"]}/>
     <Bar dataKey="incremental" fill="#3b77ae" radius={[5,5,0,0]} isAnimationActive={false}/>
    </BarChart>
   </ResponsiveContainer>
  </div>
  <div className="vse-table-overflow"><table className="vse-table">
   <thead><tr><th>Assumptions at {num(cap)} MW ceiling</th><th>Winter</th><th>Summer</th><th>Autumn</th></tr></thead>
   <tbody>{rows.map(r=><tr key={r.case}><th>{r.case}</th>{seasons.map(s=><td key={s}>{num(r[s])} MWh</td>)}</tr>)}</tbody>
  </table></div>
  <p className="vse-note">The 1,000/1,500/2,000 MW ceiling is an intentionally invented modelling bound, NOT an observed import limit or grid headroom. Project flexibility is hindsight-based and battery sizing is hypothetical. These values must not be presented as outages, economic savings, statistical confidence intervals or a 2030 forecast.</p>
 </section>
 <section className="vse-panel vse-limitations">
  <p className="vse-kicker">03 / INTERPRETATION BOUNDARIES</p><h2>What remains unknown</h2>
  {study.limitations.map((t,i)=><p key={i}>{t}</p>)}
 </section>
 </>;
}
