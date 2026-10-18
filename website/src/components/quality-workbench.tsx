"use client";
import { useState } from "react";
import { FEEDS } from "@/lib/workbench-shared";
import type { QualityRow } from "@/lib/workbench";

function dayList(end:string,n:number) {
  const finish=Date.parse(end);
  return Array.from({length:n},(_,i)=>new Date(finish-(n-i)*86400000).toISOString().slice(0,10));
}
export function QualityWorkbench({rows,to}:{rows:QualityRow[];to:string}) {
  const [selected,setSelected]=useState<QualityRow|null>(null);
  const dates=dayList(to,30);
  const key=(source:string,id:string,day:string)=>source+"|"+id+"|"+day;
  const lookup=new Map(rows.map(r=>[key(r.source,r.dataset_id,r.day_utc),r]));
  const all=rows.reduce((a,r)=>({complete:a.complete+(r.complete?1:0),partial:a.partial+(!r.complete?1:0)}),{complete:0,partial:0});
  return <section className="workbench">
    <div className="wb-heading"><div><p className="eyebrow">DATA QUALITY / OBSERVED COVERAGE</p>
      <h2>Where the evidence is complete—and where it isn't.</h2>
      <p>Every cell covers one source and one UTC calendar day. Blank cells mean <strong>no stored records</strong>, not zero demand or an ingestion failure.</p></div>
    </div>
    <div className="quality-strip">
      <div><strong>{all.complete}</strong><span>Source-days structurally complete</span></div>
      <div><strong>{all.partial}</strong><span>Source-days partial or discontinuous</span></div>
      <div><strong>{90-rows.length}</strong><span>Source-days without stored records</span></div>
    </div>
    <div className="heatmap-wrap">
      <div className="heatmap-labels" aria-hidden="true">{FEEDS.map(f=><span key={f.dataset_id}>{f.source==="fingrid"?"Fingrid":"ENTSO-E"} {f.dataset_id}</span>)}</div>
      <div className="heatmap-body">
        <div className="heatmap-dates" aria-hidden="true">{dates.map((day,i)=><span key={day}>{i%5===0?day.slice(5):""}</span>)}</div>
        {FEEDS.map(f=><div className="heatmap-row" key={f.dataset_id}>
          {dates.map(day=>{
            const row=lookup.get(key(f.source,f.dataset_id,day));
            return <button key={day} type="button"
              className={"heatmap-cell "+(!row?"none":row.complete?"complete":"partial")}
              title={day+" · "+f.label+" · "+(!row?"No stored intervals":row.intervals+" intervals; "+row.revisions+" retrieval revisions; "+(row.complete?"complete":"incomplete"))}
              aria-label={day+" "+f.label+": "+(!row?"no stored intervals":row.complete?"complete":"partial")}
              onClick={()=>setSelected(row??null)} />;
          })}
        </div>)}
      </div>
    </div>
    <div className="heatmap-legend"><span><i className="legend-complete"/>Complete day</span><span><i className="legend-partial"/>Partial or gaps</span><span><i className="legend-empty"/>No stored day</span></div>
    {selected&&<div className="evidence-drawer" role="region" aria-label="Day coverage details">
      <div className="wb-heading"><h3>{selected.day_utc} · {selected.source.toUpperCase()} {selected.dataset_id}</h3>
        <button className="text-close" type="button" onClick={()=>setSelected(null)}>Close ×</button></div>
      <p>{selected.complete?"A structurally continuous complete UTC day":"Incomplete coverage: check source intervals and reported timestamps."}</p>
      <div className="evidence-meta">
        <span><b>Distinct intervals</b>{selected.intervals}</span>
        <span><b>Stored revisions</b>{selected.revisions}</span>
        <span><b>Internal discontinuities</b>{selected.gaps}</span>
        <span><b>Last retrieved (UTC)</b>{selected.latest_retrieved.slice(0,16).replace("T"," ")}</span>
      </div>
    </div>}
    <p className="chart-caption">Completeness checks continuous, non-overlapping UTC interval boundaries for recorded source-days; Fingrid quarter-hour sources also require 96 records. A structurally complete day does not certify that the operator's numerical values are error-free.</p>
  </section>;
}
