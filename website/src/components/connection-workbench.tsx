"use client";
import { useMemo, useState } from "react";
import type { Capacity, Direction, Point } from "@/lib/types";
import { sourceReviewStatus } from "@/lib/verification";

type Choice = {pointId:string;direction:Direction;year:number};
type CoverageFilter = "all"|"recorded"|"gaps";
const directions:Direction[]=["production","consumption"];
const key=(id:string,d:Direction,y:number)=>[id,d,y].join("|");
const short=(name:string)=>name.replace(/\s+\d+\s*kV$/i,"");
const quote=(value:unknown)=>'"'+String(value??"").replace(/"/g,'""')+'"';

export function ConnectionWorkbench({points,observations,initialPointId}:{points:Point[];observations:Capacity[];initialPointId?:string}){
 const [search,setSearch]=useState(points.find(p=>p.connection_point_id===initialPointId)?.name.replace(/\s+\d+\s*kV$/i,"")??"");
 const [direction,setDirection]=useState<"both"|Direction>("both");
 const [coverage,setCoverage]=useState<CoverageFilter>("all");
 const [sort,setSort]=useState<"name"|"coverage">("name");
 const [view,setView]=useState<"matrix"|"records">("matrix");
 const [chosen,setChosen]=useState<Choice|null>(null);
 const years=useMemo(()=>{
   const found=Array.from(new Set(observations.map(o=>o.effective_year).filter((y):y is number=>y!==null))).sort((a,b)=>a-b);
   return found;
 },[observations]);
 const [recordYear,setRecordYear]=useState<number|null>(null);
 const chosenYear=recordYear!==null&&years.includes(recordYear)?recordYear:years[0]??null;
 const indexed=useMemo(()=>{
   const result=new Map<string,Capacity[]>();
   for(const o of observations){
     const k=key(o.connection_point_id,o.direction,o.effective_year??-1);
     const arr=result.get(k)??[];arr.push(o);result.set(k,arr);
   }
   return result;
 },[observations]);
 const slotsFor=(point:Point)=>years.flatMap(y=>directions.map(d=>indexed.get(key(point.connection_point_id,d,y))??[]));
 const visiblePoints=useMemo(()=>points.filter(p=>{
   if(!p.name.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase()))return false;
   const cells=years.flatMap(y=>directions.filter(d=>direction==="both"||d===direction).map(d=>indexed.get(key(p.connection_point_id,d,y))??[]));
   return coverage==="all"||(coverage==="recorded"?cells.some(c=>c.length===1):cells.some(c=>c.length!==1));
 }).sort((a,b)=>sort==="name"?a.name.localeCompare(b.name):
   slotsFor(b).filter(c=>c.length===1).length-slotsFor(a).filter(c=>c.length===1).length||a.name.localeCompare(b.name)),
 [points,search,years,indexed,coverage,direction,sort]);
 const fields=years.flatMap(y=>directions.filter(d=>direction==="both"||d===direction).map(d=>({y,d})));
 const sampleCells=points.length*years.length*2;
 const observedCells=points.reduce((n,p)=>n+years.flatMap(y=>directions.map(d=>indexed.get(key(p.connection_point_id,d,y))??[])).filter(a=>a.length===1).length,0);
 const conflicts=points.reduce((n,p)=>n+years.flatMap(y=>directions.map(d=>indexed.get(key(p.connection_point_id,d,y))??[])).filter(a=>a.length>1).length,0);
 const verified=observations.filter(o=>sourceReviewStatus(o).status==="screenshot_match").length;
 const visibleIds=new Set(visiblePoints.map(p=>p.connection_point_id));
 const recordRows=observations.filter(o=>visibleIds.has(o.connection_point_id)&&
   (direction==="both"||o.direction===direction)&&
   (chosenYear===null||o.effective_year===chosenYear))
   .sort((a,b)=>a.name.localeCompare(b.name)||a.direction.localeCompare(b.direction));
 const initial=observations.find(o=>visibleIds.has(o.connection_point_id)&&
   (direction==="both"||o.direction===direction));
 const active=chosen??(initial?{pointId:initial.connection_point_id,direction:initial.direction,year:initial.effective_year??years[0]}:null);
 const activePoint=active?points.find(p=>p.connection_point_id===active.pointId)??null:null;
 const matching=active?indexed.get(key(active.pointId,active.direction,active.year))??[]:[];
 const selectedRecord=matching.length===1?matching[0]:null;
 const grade=selectedRecord?sourceReviewStatus(selectedRecord):null;
 const select=(pointId:string,d:Direction,y:number)=>setChosen({pointId,direction:d,year:y});
 const exportRows=()=>{
   const columns=["observation_id","connection_point_id","name","voltage_kv","direction","effective_year","capacity_value","capacity_unit","source_observed_at","source_url","review_status"];
   const lines=[columns.join(","),...recordRows.map(o=>[o.observation_id,o.connection_point_id,o.name,o.voltage_kv,o.direction,o.effective_year,o.capacity_value,o.capacity_unit,o.source_observed_at,o.source_url,sourceReviewStatus(o).status].map(quote).join(","))];
   const blob=new Blob([lines.join("\r\n")],{type:"text/csv;charset=utf-8"});
   const url=URL.createObjectURL(blob);
   const a=document.createElement("a");a.href=url;a.download="finnish-grid-atlas-observations.csv";a.click();URL.revokeObjectURL(url);
 };
 return <section className="df-explorer" aria-label="Connection evidence explorer">
  <div className="df-explorer-intro">
   <div><span className="df-overline">SOURCE EVIDENCE / FINGRID GRID SCOPE</span><h2>Substation evidence explorer</h2>
   <p>Explore what was captured, inspect original observations, and identify gaps. This is a sampled record collection, not a nationwide capacity map.</p></div>
   <a href="/api/v1/export/recheck" className="button secondary">Audit worksheet ↗</a>
  </div>
  <div className="df-summary" aria-label="Evidence sample coverage">
   <div><strong>{points.length}</strong><span>Substations in catalogue</span></div>
   <div><strong>{observations.length}</strong><span>Recorded source values</span></div>
   <div><strong>{Math.max(0,sampleCells-observedCells-conflicts)}</strong><span>Not captured in sample</span></div>
   <div><strong>{verified}</strong><span>Screenshot-matched records</span></div>
  </div>
  <div className="df-definition"><strong>Coverage ≠ capacity.</strong> This comparison covers {points.length} captured substations and {years.length} recorded years, not every Finnish station or every Fingrid publication. Missing cells are <b>unknown, not zero MW</b>. No values are summed.</div>
  <div className="df-controls" aria-label="Explore evidence filters">
   <label className="df-search">Search substations<input aria-label="Filter substations by name" type="search" value={search} placeholder="Type a name…" onChange={e=>{setSearch(e.target.value);setChosen(null);}}/></label>
   <label>Direction<select value={direction} onChange={e=>{setDirection(e.target.value as typeof direction);setChosen(null);}}><option value="both">Both</option><option value="production">Production</option><option value="consumption">Consumption</option></select></label>
   <label>Coverage<select value={coverage} onChange={e=>setCoverage(e.target.value as CoverageFilter)}><option value="all">All substations</option><option value="recorded">Has recorded values</option><option value="gaps">Has uncaptured cells</option></select></label>
   <label>Sort by<select value={sort} onChange={e=>setSort(e.target.value as typeof sort)}><option value="name">Name A–Z</option><option value="coverage">Most records first</option></select></label>
  </div>
  <div className="df-toolbar">
   <div className="df-view-switch" role="group" aria-label="Evidence display">
    <button type="button" aria-pressed={view==="matrix"} className={view==="matrix"?"on":""} onClick={()=>setView("matrix")}>Year matrix</button>
    <button type="button" aria-pressed={view==="records"} className={view==="records"?"on":""} onClick={()=>setView("records")}>Source records</button>
   </div>
   <div className="df-toolbar-info">{visiblePoints.length} of {points.length} substations · {recordRows.length} source rows in {chosenYear??"all years"}</div>
  </div>
  {view==="matrix"?<div className="df-table-scroll" role="region" tabIndex={0} aria-label="Year-by-year evidence matrix, horizontally scrollable">
   <table className="df-matrix"><thead><tr><th rowSpan={2} scope="col">Substation</th>{years.map(y=><th key={y} colSpan={direction==="both"?2:1} scope="colgroup">{y}</th>)}</tr>
     <tr>{fields.map(({y,d})=><th key={y+d} scope="col">{d==="production"?"Production":"Consumption"}</th>)}</tr></thead>
    <tbody>{visiblePoints.map(p=><tr key={p.connection_point_id}><th scope="row"><strong>{short(p.name)}</strong><small>{p.voltage_kv??"—"} kV · {p.operator}</small></th>
    {fields.map(({y,d})=>{
      const entries=indexed.get(key(p.connection_point_id,d,y))??[];
      const observed=entries.length===1,ambiguous=entries.length>1;
      const isSelected=active?.pointId===p.connection_point_id&&active.year===y&&active.direction===d;
      return <td key={key(p.connection_point_id,d,y)}><button type="button" aria-pressed={isSelected} className={"df-cell "+(observed?"has-data":ambiguous?"conflict":"no-data")+(isSelected?" selected":"")} onClick={()=>select(p.connection_point_id,d,y)}
        aria-label={short(p.name)+" "+d+" "+y+": "+(observed?entries[0].capacity_value+" "+entries[0].capacity_unit:ambiguous?"multiple entries need reconciliation":"not captured")}>
         {observed?<><strong>{entries[0].capacity_value.toLocaleString("en-US")}</strong><small>{entries[0].capacity_unit} · indicative</small></>:ambiguous?<span>Needs review</span>:<span>Not captured</span>}
       </button></td>;
    })}</tr>)}</tbody></table>
   {visiblePoints.length===0&&<div className="df-empty">No substations match these filters. Try clearing the search or coverage filter.</div>}
  </div>:<div className="df-records-wrap">
   <div className="df-records-head"><label>Effective year<select aria-label="Filter source records by effective year" value={chosenYear??""} onChange={e=>setRecordYear(Number(e.target.value))}>{years.map(y=><option key={y} value={y}>{y}</option>)}</select></label>
   <button type="button" onClick={exportRows} disabled={recordRows.length===0} className="df-export">Download displayed CSV ↓</button></div>
   <div className="df-table-scroll" role="region" tabIndex={0} aria-label="Recorded capacity observations">
    <table className="df-record-table"><thead><tr><th>Substation</th><th>Direction</th><th>Effective year</th><th>Indicative figure</th><th>Review status</th><th>Inspect</th></tr></thead>
    <tbody>{recordRows.map(o=><tr key={o.observation_id}><th scope="row">{short(o.name)}</th><td>{o.direction}</td><td>{o.effective_year??"Unknown"}</td><td><strong>{o.capacity_value} {o.capacity_unit}</strong></td><td>{sourceReviewStatus(o).status==="screenshot_match"?"Screenshot matched":"Not yet audited"}</td><td><button type="button" onClick={()=>select(o.connection_point_id,o.direction,o.effective_year??years[0])}>Inspect ↗</button></td></tr>)}</tbody></table>
    {recordRows.length===0&&<div className="df-empty">No source observations match the current filters. This does not imply zero capacity.</div>}
   </div>
  </div>}
  <div className="df-detail" aria-live="polite">
   <div className="df-detail-heading"><div><span className="df-overline">SELECTED INTERSECTION / SOURCE PROVENANCE</span>
    <h3>{activePoint?short(activePoint.name):"Select an observation"}</h3>
    {active&&<p>{active.direction==="production"?"Generation / production":"Electricity consumption"} · {active.year} · {activePoint?.voltage_kv??"—"} kV</p>}</div>
    <a href="/quality#audit">Audit evidence ↗</a></div>
   {activePoint&&active?<div className="df-detail-body">
     <div className="df-primary-reading">
      <span>Indicative source figure</span><strong>{selectedRecord?selectedRecord.capacity_value.toLocaleString("en-US"):"—"}<small>{selectedRecord?selectedRecord.capacity_unit:"Not captured"}</small></strong>
      <p>{matching.length>1?"Multiple records need reconciliation before display.":selectedRecord?"Recorded in a dated Fingrid Grid Scope capture. It is not an offer of available grid headroom.":"No value for this direction and effective year is in the captured dataset. The operator may have other values."}</p>
     </div>
     <dl className="df-provenance">
      <div><dt>Source evidence</dt><dd>{selectedRecord?"Fingrid Grid Scope":"Not in compiled capture"}</dd></div>
      <div><dt>Transcription review</dt><dd>{grade?.status==="screenshot_match"?(grade.grade==="exact_tooltip"?"Screenshot tooltip matched":"Screenshot panel number matched"):"No audit for this entry"}</dd></div>
      <div><dt>Captured (UTC)</dt><dd>{selectedRecord?selectedRecord.source_observed_at.slice(0,16).replace("T"," "):"Unknown"}</dd></div>
      <div><dt>Physical connection validation</dt><dd>Not established</dd></div>
     </dl>
   </div>:<p className="df-empty">Select a cell to inspect its source and limitations.</p>}
   {activePoint&&<div className="df-detail-footer"><a href={selectedRecord?.source_url??activePoint.source_url} target="_blank" rel="noreferrer">Open Fingrid source ↗</a><span>Numbers cannot be combined between points or interpolated across years.</span></div>}
  </div>
  <div className="df-footer-notes"><strong>Interpretation rules</strong><p>These are dated transcriptions, not live offers. An unfilled cell is not a zero. Sample completeness is not national coverage; the Finnish main grid and Fingrid's capacity calculations are broader than this collected dataset. See <a href="/method">methodology</a> and <a href="/quality">data quality</a>.</p></div>
 </section>;
}
