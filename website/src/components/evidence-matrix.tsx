"use client";
import {useMemo,useState} from "react";
import Link from "next/link";
import type {Capacity,Point,Direction} from "@/lib/types";
import {sourceReviewStatus} from "@/lib/verification";

type Cell={point:Point;year:number;direction:Direction;records:Capacity[]};
const short=(name:string)=>name.replace(/\s+\d+\s*kV$/i,"");

export function EvidenceMatrix({points,observations}:{points:Point[];observations:Capacity[]}){
 const years=useMemo(()=>[...new Set(observations.map(v=>v.effective_year).filter((x):x is number=>x!==null))].sort((a,b)=>a-b),[observations]);
 const [year,setYear]=useState<number|null>(null);
 const [selection,setSelection]=useState<string|null>(null);
 const displayedYears=year===null?years:years.filter(x=>x===year);
 const cells=useMemo(()=>{
  const indexed=new Map<string,Capacity[]>();
  for(const record of observations){
   const key=[record.connection_point_id,record.effective_year,record.direction].join("|");
   indexed.set(key,[...(indexed.get(key)??[]),record]);
  }
  return points.flatMap(point=>years.flatMap(y=>(["consumption","production"] as const).map(direction=>({
   point,year:y,direction,records:indexed.get([point.connection_point_id,y,direction].join("|"))??[]
  }))));
 },[points,years,observations]);
 const keyOf=(c:Cell)=>[c.point.connection_point_id,c.year,c.direction].join("|");
 const selected=cells.find(c=>keyOf(c)===selection)??null;
 const populated=cells.filter(c=>c.records.length===1).length;
 const unresolved=cells.filter(c=>c.records.length>1).length;
 const uncaptured=cells.filter(c=>c.records.length===0).length;
 return <div className="mvp-matrix">
  <div className="mvp-matrix-top">
   <div><p className="df-overline">Sampled Grid Scope points</p>
    <h2>What is known, and where the gaps are</h2>
    <p>Each cell is one point × direction × effective year. Values are indicative source transcriptions, not connection rights or additive MW.</p></div>
   <Link href="/connections">Explore source records ↗</Link>
  </div>
  {years.length>0&&<div className="mvp-matrix-controls">
   <span>Years</span>
   <button type="button" aria-pressed={year===null} className={year===null?"selected":""} onClick={()=>{setYear(null);setSelection(null);}}>All</button>
   {years.map(y=><button type="button" key={y} aria-pressed={year===y} className={year===y?"selected":""} onClick={()=>{setYear(y);setSelection(null);}}>{y}</button>)}
   <div className="mvp-matrix-legend"><span><i className="captured"/>Captured</span><span><i className="empty"/>Not captured</span></div>
  </div>}
  {points.length===0||years.length===0?
    <p className="notice" role="status">The source records are unavailable. No indicative values have been substituted.</p>:
    <div className="mvp-matrix-grid-wrap" role="region" tabIndex={0} aria-label="Interactive source evidence by point, year and direction">
    <table className="mvp-matrix-table">
     <thead><tr><th scope="col" rowSpan={2}>Grid point</th>
      {displayedYears.map(y=><th scope="colgroup" colSpan={2} key={y}>{y}</th>)}
     </tr><tr>{displayedYears.flatMap(y=>(["consumption","production"] as const).map(d=><th key={y+d} scope="col">{d==="consumption"?"Demand":"Injection"}</th>))}</tr></thead>
     <tbody>{points.map(point=><tr key={point.connection_point_id}>
      <th scope="row"><strong>{short(point.name)}</strong><small>{point.voltage_kv??"?"} kV · {point.operator}</small></th>
      {displayedYears.flatMap(y=>(["consumption","production"] as const).map(d=>{
       const cell=cells.find(c=>c.point.connection_point_id===point.connection_point_id&&c.year===y&&c.direction===d)!;
       const record=cell.records[0],isUnique=cell.records.length===1;
       const label=isUnique?record.capacity_value+" "+record.capacity_unit:cell.records.length===0?"Not captured":"Review";
       const isSelected=selection===keyOf(cell);
       return <td key={keyOf(cell)}><button type="button" className={"mvp-matrix-cell "+(isUnique?"captured":"uncaptured")+(isSelected?" selected":"")}
        aria-pressed={isSelected} aria-label={short(point.name)+", "+y+", "+d+": "+label+". Inspect source evidence"}
        onClick={()=>setSelection(isSelected?null:keyOf(cell))}>
        {isUnique?<><strong>{record.capacity_value}</strong><small>{record.capacity_unit}</small></>:<span>{cell.records.length?"Review":"—"}</span>}
       </button></td>;
      }))}
     </tr>)}</tbody>
    </table>
   </div>}
  {selected&&<div className="mvp-matrix-detail" aria-live="polite">
   <div><span className="df-overline">Selected record</span><strong>{short(selected.point.name)} · {selected.year} · {selected.direction==="consumption"?"Demand":"Injection"}</strong>
    {selected.records.length===1?<p>
      <b>{selected.records[0].capacity_value} {selected.records[0].capacity_unit}</b> · Indicative Grid Scope value · {sourceReviewStatus(selected.records[0]).status==="screenshot_match"?"Screenshot transcription matched":"Source transcription not independently matched"} · Captured {selected.records[0].source_observed_at.slice(0,10)}.
     </p>:<p>{selected.records.length===0?"No matching value in the captured sample; unknown, not zero.":"Multiple source values require reconciliation before use."}</p>}
   </div>
   <div className="mvp-matrix-detail-actions">
    {selected.records.length===1&&<a target="_blank" rel="noreferrer" href={selected.records[0].source_url}>Original source ↗</a>}
    <Link href={"/connections?point_id="+encodeURIComponent(selected.point.connection_point_id)}>View point ↗</Link>
    <button type="button" onClick={()=>setSelection(null)} aria-label="Close selected record">×</button>
   </div>
  </div>}
  <footer className="mvp-matrix-footer">
   <span><b>{populated}</b> captured / <b>{cells.length}</b> possible sample cells · {uncaptured} uncaptured{unresolved?" · "+unresolved+" require review":""}</span>
   <span>Unknown ≠ 0 MW · Source snapshot ≠ connection approval</span>
  </footer>
 </div>;
}
