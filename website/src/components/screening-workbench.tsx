"use client";
import {useMemo,useState} from "react";
import Link from "next/link";
import type {Capacity,Point} from "@/lib/types";
import {screenRecords,type ScreeningInput,type ScreeningRow,type EvidenceStatus} from "@/lib/screening";

const labels:Record<EvidenceStatus,string>={
 indicative_threshold_met:"Indicative threshold met",
 indicative_below_request:"Below indicative threshold",
 unknown_not_captured:"No corresponding observation",
 needs_source_review:"Needs source review",
 conflicting_evidence:"Conflicting captured evidence",
 unit_not_comparable:"Unit not comparable"
};
const groupOrder:EvidenceStatus[]=[
 "indicative_threshold_met","indicative_below_request","unknown_not_captured",
 "needs_source_review","conflicting_evidence","unit_not_comparable"
];
const quote=(x:unknown)=>'"'+String(x??"").replace(/"/g,'""')+'"';
function exportRows(input:ScreeningInput,rows:ScreeningRow[]){
 const fields=["requested_mw","target_year","requested_direction","voltage_filter","connection_point_id",
 "name","voltage_kv","evidence_status","feasibility","capacity_value","capacity_unit",
 "connection_type","connection_pathway","pathway_note","timing_evidence","reinforcement_verified","next_actions",
 "observation_id","source_observed_at","source_review","source_review_grade","source_review_date",
 "source_url","validity_notes","interpretation"];
 const values=rows.map(r=>[
  input.demand_mw,input.year,input.direction,input.voltage,r.connection_point_id,r.name,
  r.voltage_kv,r.evidence_status,r.feasibility,r.capacity_value,r.capacity_unit,
  input.connection_type,r.connection_pathway,r.pathway_note,r.timing_evidence,
  r.verified_reinforcement_for_this_point,r.next_actions.join("; "),
  r.observation_id,r.source_observed_at,r.source_review,r.source_review_grade,r.source_review_date,
  r.source_url,r.validity_notes,
  "Evidence-only. Published indicative estimate does not establish 100 MW feasibility or connection rights."
 ]);
 const csv=[fields.map(quote).join(","),...values.map(a=>a.map(quote).join(","))].join("\r\n")+"\r\n";
 const blob=new Blob(["\ufeff"+csv],{type:"text/csv;charset=utf-8"});
 const url=URL.createObjectURL(blob);
 const anchor=document.createElement("a");
 anchor.href=url;anchor.download="finnish-grid-screening-"+input.year+"-"+input.demand_mw+"MW.csv";
 anchor.click();URL.revokeObjectURL(url);
}
function downloadBrief(input:ScreeningInput,rows:ScreeningRow[]){
 const lines=[
 "# Finnish Grid Atlas: connection-readiness evidence brief",
 "",
 "Requested: "+input.demand_mw+" MW "+input.direction+"; effective year "+input.year+
 "; voltage filter "+input.voltage+"; proposed "+input.connection_type+" connection.",
 "",
 "**Evidence triage only. No site feasibility, operator approval, reservable MW or queue position.**",
 "Official pathway: https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/",
 ""
 ];
 for(const r of rows)lines.push("## "+r.name,
  "Indicative value: "+(r.capacity_value===null?"Not captured":r.capacity_value+" "+r.capacity_unit),
  "Source evidence: "+r.evidence_status,
  "Fingrid pathway: "+r.connection_pathway,
  "Pathway note: "+r.pathway_note,
  "Effective-year evidence: "+r.timing_evidence,
  "Snapshot: "+(r.source_observed_at??"Not captured"),
  "Source link: "+(r.source_url??"Not captured"),
  "Verified linked reinforcement: No",
  "Operator-approved connection: No claim",
  "Next action: "+r.next_actions.join(" "),
  "");
 const blob=new Blob([lines.join("\n")],{type:"text/markdown;charset=utf-8"});
 const href=URL.createObjectURL(blob),anchor=document.createElement("a");
 anchor.href=href;anchor.download="finnish-grid-readiness-"+input.year+"-"+input.demand_mw+"MW.md";
 anchor.click();URL.revokeObjectURL(href);
}
export function ScreeningWorkbench({points,observations,initial}:{points:Point[];observations:Capacity[];initial:ScreeningInput}){
 const [demand,setDemand]=useState(String(initial.demand_mw));
 const [year,setYear]=useState(initial.year);
 const [voltage,setVoltage]=useState<ScreeningInput["voltage"]>(initial.voltage);
 const [connectionType,setConnectionType]=useState<ScreeningInput["connection_type"]>(initial.connection_type);
 const [expanded,setExpanded]=useState<string|null>(null);
 const number=Number(demand);
 const valid=/^(?:\d+(?:\.\d+)?|\.\d+)$/.test(demand)&&Number.isFinite(number)&&number>0&&number<=10000;
 const criteria:ScreeningInput={demand_mw:valid?number:100,year,direction:"consumption",voltage,connection_type:connectionType};
 const report=useMemo(()=>valid?screenRecords(points,observations,criteria):null,
  [points,observations,valid,number,year,voltage,connectionType]);
 const params=new URLSearchParams({demand_mw:String(number),year:String(year),direction:"consumption",voltage:String(voltage),connection_type:connectionType});
 const availableYears=Array.from(new Set([2026,2030,2035,...observations.map(o=>o.effective_year).filter((y):y is number=>y!==null)])).sort((a,b)=>a-b);
 return <>
 <div className="sc-lab">
  <section className="sc-form" aria-label="Electricity connection screening request">
   <div className="sc-section-top"><p className="sc-eyebrow">01 / SCENARIO INPUT</p><span>No grid-model assumptions added</span></div>
   <div className="sc-form-grid">
    <label>Requested load <span>MW · electricity consumption</span>
      <input value={demand} onChange={e=>{setDemand(e.target.value);setExpanded(null);}} type="number" min="0.001" max="10000" step="any" inputMode="decimal" aria-invalid={!valid} aria-describedby="sc-demand-help"/>
    </label>
    <label>Effective year <span>Exact source year; no interpolation</span>
     <select value={year} onChange={e=>{setYear(Number(e.target.value));setExpanded(null);}}>
      {availableYears.map(y=><option value={y} key={y}>{y}</option>)}
     </select>
    </label>
    <label>Voltage preference <span>Filter within the sampled points</span>
     <select value={voltage} onChange={e=>{const s=e.target.value;setVoltage(s==="all"?"all":Number(s) as 110|220|400);setExpanded(null);}}>
      <option value="all">All recorded point voltages</option><option value="400">400 kV</option><option value="220">220 kV</option><option value="110">110 kV</option>
     </select>
    </label>
    <label>Proposed arrangement <span>Fingrid planning guidance</span>
     <select value={connectionType} onChange={e=>{setConnectionType(e.target.value as ScreeningInput["connection_type"]);setExpanded(null);}}>
      <option value="switchyard">Switchyard</option>
      <option value="line">Transmission line</option>
      <option value="unspecified">Not determined</option>
     </select>
    </label>
   </div>
   <p className="sc-fieldnote" id="sc-demand-help">{valid?"100 MW is the default illustrative request; changing the input reruns evidence classification only.":"Enter a positive requested load no greater than 10,000 MW."}</p>
  </section>
  {report?<section className="sc-output">
    <div className="sc-section-top"><p className="sc-eyebrow">02 / EVIDENCE RESULTS</p><span>Research sample · not national coverage</span></div>
    <div className="sc-headline"><div><h2>{report.summary.indicative_threshold_met} threshold matches</h2><p>For {number} MW consumption in {year}; {voltage==="all"?"any sampled voltage":voltage+" kV"}.</p></div><div className="sc-readout"><span>{report.scope.sampled_connection_points} screened</span><span>{report.summary.unknown_not_captured} unknown</span><span>0 feasibility assessed</span></div></div>
    <p className="notice warn"><strong>Voltage review:</strong> {report.results.filter(r=>r.connection_pathway==="review_lower_voltage_switchyard").length} sampled 400-kV-labelled points need lower-voltage switchyard arrangements checked for this load. Threshold matches and source MW values are unchanged.</p>
    <div className="sc-summary-grid">
      <div><strong>{report.summary.indicative_threshold_met}</strong><span>Published estimate ≥ requested MW</span></div>
      <div><strong>{report.summary.indicative_below_request}</strong><span>Below indicative threshold</span></div>
      <div><strong>{report.summary.unknown_not_captured}</strong><span>No exact observation</span></div>
      <div><strong>{report.summary.needs_source_review+report.summary.conflicting_evidence+report.summary.unit_not_comparable}</strong><span>Review / units / conflicts</span></div>
    </div>
    <div className="sc-results-toolbar"><strong>Evidence and next actions</strong><div><button type="button" onClick={()=>downloadBrief(criteria,report.results)}>Readiness brief ↓</button><a href={"/api/v1/screening?"+params.toString()} target="_blank" rel="noreferrer">Open JSON ↗</a><button type="button" onClick={()=>exportRows(criteria,report.results)}>Export evidence CSV ↓</button></div></div>
    {report.results.length? <div className="sc-results">
      {groupOrder.flatMap(status=>report.results.filter(r=>r.evidence_status===status)).map(r=><article key={r.connection_point_id} className="sc-result">
       <div className="sc-result-main">
        <div className="sc-result-name"><span className="sc-point-mark" aria-hidden="true"/><div><h3>{r.name}</h3><small>{r.operator} · {r.voltage_kv??"Unknown"} kV · Source capture {r.source_observed_at?new Date(r.source_observed_at).toISOString().slice(0,10):"not available for requested year"}</small></div></div>
        <div className="sc-result-status"><span className={"sc-status "+(r.evidence_status==="indicative_threshold_met"?"matched":r.evidence_status==="unknown_not_captured"?"unknown":"review")}>{labels[r.evidence_status]}</span><strong>{r.capacity_value!==null?r.capacity_value+" "+r.capacity_unit:"—"}</strong></div>
        <button type="button" aria-expanded={expanded===r.connection_point_id} onClick={()=>setExpanded(expanded===r.connection_point_id?null:r.connection_point_id)}>{expanded===r.connection_point_id?"Hide provenance −":"Inspect evidence +"}</button>
       </div>
       {expanded===r.connection_point_id&&<div className="sc-provenance">
        <div><span>Evidence classification</span><strong>{labels[r.evidence_status]}</strong></div>
        <div><span>Engineering feasibility</span><strong>Not assessed · no capacity reservation</strong></div>
        <div><span>Fingrid pathway guidance</span><strong>{r.connection_pathway.replaceAll("_"," ")}</strong></div>
        <p><strong>Voltage and arrangement:</strong> {r.pathway_note} <a href={r.pathway_source_url} target="_blank" rel="noreferrer">Official rules ↗</a></p>
        <p><strong>Next action:</strong> {r.next_actions.join(" ")}</p>
        <div><span>Target-year source capture</span><strong>{r.timing_evidence==="exact_year_capture"?"Captured / recheck source age":"Not captured"}</strong></div>
        <div><span>Verified point-specific reinforcement</span><strong>None documented</strong></div>
        <div><span>Source review</span><strong>{r.source_review==="screenshot_match"?"Original screenshot transcription matched ("+(r.source_review_grade??"")+")":r.source_review==="not_audited"?"Not independently screenshot reviewed":"No captured estimate"}</strong></div>
        <div><span>Captured at (UTC)</span><strong>{r.source_observed_at??"Not captured"}</strong></div>
        <div><span>Observation identifier</span><strong>{r.observation_id??"None"}</strong></div>
        <div><span>Effective year and direction</span><strong>{year} · consumption</strong></div>
        <p>{r.validity_notes??"This particular intersection was not captured. Missing evidence is neither zero capacity nor a negative grid-feasibility finding."}</p>
        {r.source_url&&<a href={r.source_url} target="_blank" rel="noreferrer">Open original Fingrid viewer ↗</a>}
       </div>}
      </article>)}
     </div>:<p className="sc-no-results">No recorded connection points match this voltage filter. The historical 128-row designation archive is not silently added to screening; this does not mean no such stations exist in Finland.</p>}
    <div className="sc-limit"><strong>Source evidence ≠ feasibility.</strong> A 400 MW indicative Grid Scope observation is neither a guaranteed 400 MW connection offer nor evidence of 300 MW reservable capacity after considering this request. Missing years stay unknown. These points are not geographically ranked.</div>
   </section>:<p className="notice warn" role="alert">Cannot screen with this input. Use a positive requested MW up to 10,000.</p>}
 </div>
 <div className="sc-archive-note"><span>Historical inventory is separate:</span> <Link href="/stations">Browse the 128 archived station-name rows ↗</Link><p>The historical list lacks verified current status and site-specific consumption estimates. It cannot increase the number of screenable points.</p></div>
 </>;
}
