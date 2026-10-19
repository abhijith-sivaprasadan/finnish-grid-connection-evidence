"use client";
import { useMemo, useState } from "react";
type Station={id:string;name:string;voltage_kv:number;source_url:string;notes:string};
const slug=(v:string)=>v.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLocaleLowerCase("en");
export function StationInventoryExplorer({rows}:{rows:Station[]}){
 const [term,setTerm]=useState("");
 const [voltage,setVoltage]=useState("all");
 const [sort,setSort]=useState<"name"|"voltage">("name");
 const [page,setPage]=useState(0);
 const [selected,setSelected]=useState<string|null>(null);
 const pageSize=25;
 const matches=useMemo(()=>rows.filter(r=>(voltage==="all"||String(r.voltage_kv)===voltage)&&slug(r.name).includes(slug(term.trim()))).sort((a,b)=>sort==="name"?a.name.localeCompare(b.name,"fi")||b.voltage_kv-a.voltage_kv:b.voltage_kv-a.voltage_kv||a.name.localeCompare(b.name,"fi")),[rows,term,voltage,sort]);
 const pages=Math.max(1,Math.ceil(matches.length/pageSize));
 const activePage=Math.min(page,pages-1);
 const visible=matches.slice(activePage*pageSize,(activePage+1)*pageSize);
 const focus=selected?rows.find(r=>r.id===selected):null;
 const filterChange=()=>{setPage(0);setSelected(null);};
 const counts=(v:number)=>rows.filter(r=>r.voltage_kv===v).length;
 return <section className="si-inventory" aria-label="Fingrid substation designation archive">
  <div className="si-kpis" aria-label="Historical listed rows by voltage">
   <div><small>Individually listed station rows</small><strong>{rows.length}</strong><span>Source printed total: 127 · discrepancy open</span></div>
   <div><small>400 kV</small><strong>{counts(400)}</strong><span>Named historical entries</span></div>
   <div><small>220 kV</small><strong>{counts(220)}</strong><span>Named historical entries</span></div>
   <div><small>110 kV</small><strong>{counts(110)}</strong><span>Source subtotal says 65</span></div>
  </div>
  <div className="si-controls">
   <label>Search archive<input type="search" aria-label="Search station names" placeholder="Station name…" value={term} onChange={e=>{setTerm(e.target.value);filterChange();}}/></label>
   <label>Voltage class<select aria-label="Filter station voltage class" value={voltage} onChange={e=>{setVoltage(e.target.value);filterChange();}}><option value="all">All classes</option><option value="400">400 kV</option><option value="220">220 kV</option><option value="110">110 kV</option></select></label>
   <label>Sort<select aria-label="Sort stations" value={sort} onChange={e=>{setSort(e.target.value);setPage(0);}}><option value="name">Station name</option><option value="voltage">Highest voltage</option></select></label>
   <div className="si-controls-summary" role="status">{matches.length} matching rows in historical appendix</div>
  </div>
  <div className="si-scroll" role="region" tabIndex={0} aria-label="Historical station inventory table">
   <table className="si-table"><thead><tr><th scope="col">Station label in source</th><th scope="col">Listed voltage</th><th scope="col">Source status</th><th scope="col">Details</th></tr></thead><tbody>
    {visible.map(r=><tr key={r.id}><th scope="row"><strong>{r.name}</strong><small>Local record · not an operator-issued ID</small></th><td><span className="si-voltage">{r.voltage_kv} kV</span></td><td><span className="si-historical">Historical transcription</span></td><td><button type="button" aria-pressed={selected===r.id} onClick={()=>setSelected(selected===r.id?null:r.id)}>Inspect ↗</button></td></tr>)}
   </tbody></table>
   {matches.length===0&&<div className="si-empty">No historical station name matches these filters. This does not imply the station does not exist.</div>}
  </div>
  <div className="si-pager"><span>Showing {matches.length?activePage*pageSize+1:0}–{Math.min(matches.length,(activePage+1)*pageSize)} of {matches.length}</span><div><button type="button" disabled={activePage===0} onClick={()=>{setPage(p=>Math.max(0,p-1));setSelected(null);}}>Previous</button><span>Page {activePage+1} of {pages}</span><button type="button" disabled={activePage+1>=pages} onClick={()=>{setPage(p=>p+1);setSelected(null);}}>Next</button></div></div>
  {focus&&<section className="si-detail" aria-live="polite" aria-label="Selected source station"><div className="si-detail-title"><div><p className="eyebrow">HISTORICAL SOURCE RECORD</p><h3>{focus.name}</h3></div><button type="button" onClick={()=>setSelected(null)}>Close ×</button></div>
   <dl><div><dt>Listed voltage</dt><dd>{focus.voltage_kv} kV</dd></div><div><dt>Document context</dt><dd>2024 designation annex · table headed 1.1.2020</dd></div><div><dt>Current station status</dt><dd>Not checked in this archive</dd></div><div><dt>Published MW in this record</dt><dd>None · not a capacity dataset</dd></div></dl>
   <p>{focus.notes}</p><a target="_blank" rel="noreferrer" href={focus.source_url}>View original Fingrid appendix ↗</a></section>}
 </section>;
}
