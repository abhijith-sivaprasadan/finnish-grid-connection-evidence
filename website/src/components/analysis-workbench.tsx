"use client";
import {useMemo,useState} from "react";
import {ResponsiveContainer,LineChart,Line,XAxis,YAxis,CartesianGrid,Tooltip,Legend,BarChart,Bar} from "recharts";
type SourceRow={timestamp_utc:string;consumption_mw:number;production_mw:number;consumption_retrieved_at:string;production_retrieved_at:string};
type Source={data_kind:string;time_series:SourceRow[];source_unit:string};
type Result={scenario:string;solver_status:string;termination:string;observed_load_mwh:number;observed_production_mwh:number;new_demand_mwh:number;assumed_balancing_support_mwh:number;modelled_shortfall_under_assumption_mwh:number;assumed_surplus_disposal_mwh:number;battery_charge_mwh:number;battery_discharge_mwh:number;max_balancing_support_mw:number;max_model_balance_error_mw:number;proxy_dispatch_index_units:number;window_hours:number;historical_interval_count:number};
type Report={publication_status:string;model_version:string;computed_by:string;source_job_url:string;observed_input_sha256:string;scenarios:Result[];limitations:string[];assumptions:{balancing_support_limit_mw:number;additional_load_mw:number;battery_power_mw:number;battery_usable_energy_mwh:number;battery_round_trip_efficiency:number;hypothetical_flexible_min_mw:number;hypothetical_flexible_max_mw:number}};
const names:Record<string,string>={
 observed_reference:"Observed reference",
 flat_100mw:"Continuous +100 MW",
 flexible_100mw:"Flexible +100 MW (same energy)",
 flat_100mw_with_battery:"Continuous +100 MW with storage"
};
const fmt=(x:number,d=1)=>x.toLocaleString("en-US",{maximumFractionDigits:d});
export function AnalysisWorkbench({observed,model}:{observed:Source;model:Report}){
 const [choice,setChoice]=useState("flat_100mw");
 const selected=model.scenarios.find(s=>s.scenario===choice)??model.scenarios[0];
 const baseline=model.scenarios.find(s=>s.scenario==="observed_reference")??model.scenarios[0];
 const chart=useMemo(()=>{
  const points=observed.time_series;
  const hours=[];
  for(let i=0;i<points.length;i+=4){
   const group=points.slice(i,i+4);
   const avg=(name:"consumption_mw"|"production_mw")=>Math.round(group.reduce((sum,x)=>sum+x[name],0)/group.length);
   hours.push({time:group[0].timestamp_utc.slice(5,16).replace("T"," "),consumption:avg("consumption_mw"),production:avg("production_mw")});
  }
  return hours;
 },[observed]);
 const comparison=model.scenarios.map(s=>({name:s.scenario==="observed_reference"?"Reference":s.scenario==="flat_100mw"?"Flat 100 MW":s.scenario==="flexible_100mw"?"Flexible":"Battery",shortfall:Math.round(s.modelled_shortfall_under_assumption_mwh),support:Math.round(s.assumed_balancing_support_mwh)}));
 const delta=selected?selected.modelled_shortfall_under_assumption_mwh-baseline.modelled_shortfall_under_assumption_mwh:null;
 const csv=()=>{
  const header=["scenario","model_shortfall_mwh_under_assumed_limit","assumed_balancing_supply_mwh","new_load_mwh","battery_charge_mwh","battery_discharge_mwh","model_category","source_dates","is_operator_feasibility"];
  const lines=model.scenarios.map(s=>[s.scenario,s.modelled_shortfall_under_assumption_mwh,s.assumed_balancing_support_mwh,s.new_demand_mwh,s.battery_charge_mwh,s.battery_discharge_mwh,"hypothetical PyPSA sensitivity","2026-10-15/16 UTC","false"]);
  const quote=(v:unknown)=>'"'+String(v??"").replaceAll('"','""')+'"';
  const output=[header,...lines].map(row=>row.map(quote).join(",")).join("\r\n")+"\r\n";
  const url=URL.createObjectURL(new Blob(["\ufeff"+output],{type:"text/csv;charset=utf-8"}));
  const a=document.createElement("a");a.href=url;a.download="finland_pypsa_historical_100MW_scenarios.csv";a.click();URL.revokeObjectURL(url);
 };
 return <>
  <section className="an-methodology" aria-label="Source and scenario classification">
    <div><small>OBSERVED NATIONAL INPUTS</small><strong>Fingrid 124 + 74</strong><span>Two real days; mean power by 15-minute interval</span></div>
    <div><small>MODEL RESOLUTION</small><strong>1 Finland bus</strong><span>No substation or transmission network representation</span></div>
    <div><small>ASSUMED BALANCING CEILING</small><strong>{fmt(model.assumptions.balancing_support_limit_mw,0)} MW</strong><span>Stress-test constraint — not a grid fact</span></div>
    <div><small>SHORTFALL INTERPRETATION</small><strong>Model relaxation</strong><span>Not real unserved energy in Finland</span></div>
  </section>
  <section className="an-pane">
   <div className="an-pane-top"><div><p className="an-kicker">01 / HISTORICAL INPUT CHRONOLOGY</p><h2>Observed electricity system</h2><p>Hourly means for visibility, calculated from 192 original 15-minute readings. Never a forecast of 2030.</p></div><span className="an-pill">SOURCE OBSERVATIONS</span></div>
   <div className="an-chart">
    <ResponsiveContainer width="100%" height="100%">
     <LineChart data={chart} margin={{left:5,right:14,top:9,bottom:15}}>
      <CartesianGrid stroke="#e3ecf5" vertical={false}/>
      <XAxis dataKey="time" interval={7} angle={-23} textAnchor="end" height={52} tick={{fontSize:10,fill:"#617d98"}}/>
      <YAxis domain={["auto","auto"]} tick={{fontSize:10,fill:"#617d98"}} width={60}/>
      <Tooltip formatter={(v,name)=>[fmt(Number(v),0)+" MW",String(name)]}/>
      <Legend verticalAlign="top" height={34}/>
      <Line dataKey="consumption" name="Fingrid consumption" stroke="#296aa8" dot={false} strokeWidth={2} isAnimationActive={false}/>
      <Line dataKey="production" name="Fingrid production" stroke="#65b2cf" dot={false} strokeWidth={2} isAnimationActive={false}/>
     </LineChart>
    </ResponsiveContainer>
   </div>
   <p className="an-caption">Time axis: 15–16 October 2026, UTC. Aggregate consumption is derived by Fingrid from production and cross-border flows; aggregate production is not individually dispatchable generation capacity. Mean MWh/h is numerically MW over the interval.</p>
  </section>
  <section className="an-pane">
   <div className="an-pane-top"><div><p className="an-kicker">02 / OPTIMIZED SCENARIOS</p><h2>Constraint sensitivity</h2><p>Four PyPSA 1.4 + HiGHS optimal solves. The added load always totals 4,800 MWh over 48 hours, except in the historical reference.</p></div><a className="an-quiet-link" href={model.source_job_url} target="_blank" rel="noreferrer">Solver verification ↗</a></div>
   <div className="an-scenario-picker" role="group" aria-label="Select model scenario">
    {model.scenarios.map(s=><button type="button" key={s.scenario} className={choice===s.scenario?"current":""} onClick={()=>setChoice(s.scenario)} aria-pressed={choice===s.scenario}>{names[s.scenario]??s.scenario}</button>)}
   </div>
   {selected&&<div className="an-results">
    <div><small>ADDED PROJECT ENERGY</small><strong>{fmt(selected.new_demand_mwh,0)} <em>MWh</em></strong><span>Over exactly 48 observed hours</span></div>
    <div><small>HYPOTHETICAL BALANCING SUPPLY</small><strong>{fmt(selected.assumed_balancing_support_mwh,1)} <em>MWh</em></strong><span>Modelled exchange-equivalent support, not observed imports</span></div>
    <div><small>SHORTFALL UNDER ASSUMED CAP</small><strong>{fmt(selected.modelled_shortfall_under_assumption_mwh,1)} <em>MWh</em></strong><span>{delta===null?"—":(delta>=0?"+":"")+fmt(delta,1)+" MWh versus reference"} · not actual outages</span></div>
    <div><small>BATTERY THROUGHPUT</small><strong>{fmt(selected.battery_discharge_mwh,1)} <em>MWh</em></strong><span>Discharged energy; charge {fmt(selected.battery_charge_mwh,1)} MWh</span></div>
   </div>}
   <div className="an-mini-layout">
    <div className="an-chart an-chart-small">
     <ResponsiveContainer width="100%" height="100%">
      <BarChart data={comparison} margin={{left:12,top:5,right:20,bottom:20}}>
       <CartesianGrid stroke="#e8eef5" vertical={false}/>
       <XAxis dataKey="name" tick={{fontSize:10,fill:"#69829b"}}/>
       <YAxis tick={{fontSize:10,fill:"#69829b"}} width={54}/>
       <Tooltip formatter={v=>[fmt(Number(v),1)+" MWh","Modelled shortfall under assumed cap"]}/>
       <Bar dataKey="shortfall" name="Hypothetical shortfall MWh" fill="#487ba8" radius={[5,5,0,0]} isAnimationActive={false}/>
      </BarChart>
     </ResponsiveContainer>
    </div>
    <aside className="an-scenario-detail">
     <p className="an-kicker">ASSUMPTIONS / DO NOT OVERINTERPRET</p>
     <p><strong>Constant load:</strong> 100 MW every quarter hour.</p>
     <p><strong>Flexible case:</strong> 150 MW during the lower-residual half of each day, 50 MW during the other half. Same 2,400 MWh daily project demand, but hypothetical flexibility.</p>
     <p><strong>Battery case:</strong> 100 MW / 400 MWh, assumed 90% round-trip efficiency, cyclic state of charge. No claim of commercial economics or actual site availability.</p>
     <p>Dispatch is optimized under a <strong>hypothetical 1,500 MW support cap</strong> and dimensionless stress-cost proxy. Unserved slack represents stress within that invented test, not electricity outages.</p>
    </aside>
   </div>
   <div className="an-output-actions"><a href="/api/v1/model/finland" target="_blank" rel="noreferrer">Source-attributed model JSON ↗</a><button type="button" onClick={csv}>Export solved scenario CSV ↓</button></div>
  </section>
  <section className="an-limit">
   <h2>What the model does not know</h2>
   <p>{model.limitations.join(" ")}</p>
   <div><span>Input SHA-256: <code>{model.observed_input_sha256}</code></span><span>{model.computed_by} · <strong>verified solver output</strong></span></div>
  </section>
 </>;
}
