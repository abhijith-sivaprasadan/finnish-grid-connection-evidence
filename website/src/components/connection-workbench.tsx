"use client";
import { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Capacity,Point } from "@/lib/types";
import { YEARS } from "@/lib/workbench-shared";

type Slot = {point:Point; year:number; direction:"consumption"|"production"; value:Capacity|null};
const order:["production","consumption"]=["production","consumption"];
export function ConnectionWorkbench({points,observations,initialPointId}:{points:Point[];observations:Capacity[];initialPointId?:string}) {
  const [year,setYear]=useState<number>(2026);
  const [search,setSearch]=useState(points.find(p=>p.connection_point_id===initialPointId)?.name.replace(" 400 kV","")??"");
  const [direction,setDirection]=useState<"both"|"production"|"consumption">("both");
  const [selected,setSelected]=useState<Slot|null>(null);
  const [sort,setSort]=useState<"name"|"observed">("name");
  const byKey=useMemo(()=>{
    const map=new Map<string,Capacity[]>();
    for(const observation of observations) {
      const key=[observation.connection_point_id,observation.direction,observation.effective_year].join("|");
      map.set(key,[...(map.get(key)||[]),observation]);
    }
    return map;
  },[observations]);
  const lookup=(p:Point,d:"consumption"|"production",y:number) => {
    const r=byKey.get([p.connection_point_id,d,y].join("|"))||[];
    return r.length===1?r[0]:null; // duplicates require reconciliation, not arbitrary latest
  };
  const ordered=useMemo(()=>[...points].sort((a,b)=>sort==="name"?
    a.name.localeCompare(b.name):
    observations.filter(o=>o.connection_point_id===b.connection_point_id).length-
    observations.filter(o=>o.connection_point_id===a.connection_point_id).length||a.name.localeCompare(b.name)),[points,observations,sort]);
  const filtered=ordered.filter(p=>p.name.toLocaleLowerCase().includes(search.toLocaleLowerCase().trim()));
  const bars=filtered.map(p=>({
    name:p.name.replace(" 400 kV",""),
    production:lookup(p,"production",year)?.capacity_value??null,
    consumption:lookup(p,"consumption",year)?.capacity_value??null
  }));
  const fields=YEARS.flatMap(y=>order.map(d=>({year:y,direction:d}))).filter(x=>direction==="both"||x.direction===direction);
  const activeStatus=selected?.value?"Published indicative transcription":"Not recorded in this capture";
  return <section className="workbench" aria-label="Connection evidence workbench">
    <div className="wb-heading"><div><p className="eyebrow">EVIDENCE WORKBENCH / 01</p>
      <h2>Every point. Every direction. Every recorded year.</h2>
      <p>Compare the <strong>presence of source evidence</strong>, not connection offers. A blank cell is not zero.</p></div>
      <a className="button secondary" href="/api/v1/export/recheck">Download independent audit worksheet ↓</a>
    </div>
    <div className="wb-controls">
      <label className="wb-search-label">Find a point
        <input type="search" value={search} onChange={e=>{setSearch(e.target.value);setSelected(null);}} placeholder="Search substation name…" aria-label="Filter substations by name"/>
      </label>
      <label>Matrix view
        <select value={direction} onChange={e=>{setDirection(e.target.value as typeof direction);setSelected(null);}}>
          <option value="both">Both directions</option><option value="production">Production only</option><option value="consumption">Consumption only</option>
        </select>
      </label>
      <label>Order points
        <select value={sort} onChange={e=>setSort(e.target.value as typeof sort)}>
          <option value="name">Alphabetical</option><option value="observed">Most recorded intersections</option>
        </select>
      </label>
      <div className="wb-key"><span className="wb-key-dot" />Source-transcribed MW <span className="wb-key-blank" />Unrecorded</div>
    </div>
    <div className="matrix-count">{filtered.length} of {points.length} selected substations <span>· Cell selection reveals its recorded evidence</span></div>
    <div className="matrix-scroll"><table className="capacity-matrix">
      <thead><tr><th scope="col">Fingrid 400 kV point</th>
      {fields.map(f=><th key={f.year+f.direction} scope="col">{f.year}<small>{f.direction}</small></th>)}</tr></thead>
      <tbody>{filtered.map(p=><tr key={p.connection_point_id}><th scope="row">{p.name.replace(" 400 kV","")}<small>400 kV · {p.operator}</small></th>
        {fields.map(({year:y,direction:d})=>{
          const key=p.connection_point_id+y+d;
          const matches=byKey.get([p.connection_point_id,d,y].join("|"))||[];
          const value=matches.length===1?matches[0]:null;
          const ambiguous=matches.length>1;
          return <td key={key}>
            <button type="button" className={"matrix-cell "+(value?"recorded":ambiguous?"ambiguous":"absent")}
              onClick={()=>setSelected({point:p,year:y,direction:d,value})}
              aria-label={p.name+" "+y+" "+d+": "+(value?value.capacity_value+" "+value.capacity_unit:ambiguous?"multiple captures need reconciliation":"not recorded in capture")}>
              {value?<><strong>{value.capacity_value}</strong><small>{value.capacity_unit}</small></>:ambiguous?"Review":"—"}
            </button>
          </td>;
        })}</tr>)}</tbody>
    </table></div>
    {filtered.length===0&&<p className="notice">No matching substations. Clear the search to restore the original sample.</p>}
    <p className="chart-caption">The 2026, 2030 and 2035 columns are discrete published effective years. Do not interpolate across years or add point values. Multiple observations for one intersection require reconciliation.</p>
    {selected&&<div className="evidence-drawer" role="region" aria-label="Selected evidence details">
      <div className="wb-heading">
        <div><span className="eyebrow">SELECTED EVIDENCE</span><h3>{selected.point.name} · {selected.year} · {selected.direction}</h3></div>
        <button className="text-close" onClick={()=>setSelected(null)} type="button">Close ×</button>
      </div>
      <p><strong>{activeStatus}.</strong> {selected.value?selected.value.capacity_value+" "+selected.value.capacity_unit+" was transcribed from Grid Scope.": "No value was recorded for this intersection in the published project sample."}</p>
      {selected.value&&<div className="evidence-meta">
        <span><b>Capture (UTC)</b>{selected.value.source_observed_at.replace("T"," ").slice(0,16)}</span>
        <span><b>Independent recheck</b>Pending · no reviewer confirmation</span>
        <span><b>Evidence status</b>Published indicative only</span>
        <a href={selected.value.source_url} target="_blank" rel="noreferrer">Open operator viewer ↗</a>
      </div>}
      <p className="small-note">Checking the public map is a verification of the published transcription only. It cannot guarantee physical connectability or queue allocation.</p>
    </div>}
    <div className="wb-chart-row">
      <div className="wb-chart-title">
        <div><p className="eyebrow">DISCRETE COMPARISON</p><h3>Production versus consumption</h3></div>
        <label>Effective year <select value={year} onChange={e=>setYear(Number(e.target.value))}>
          {YEARS.map(y=><option key={y}>{y}</option>)}</select></label>
      </div>
      <div className="wb-chart"><ResponsiveContainer width="100%" height={350}>
        <BarChart data={bars} margin={{top:8,right:15,left:0,bottom:35}} barCategoryGap="22%">
          <CartesianGrid vertical={false} stroke="#e6eef8"/>
          <XAxis dataKey="name" angle={-18} textAnchor="end" height={58} interval={0} tick={{fontSize:11,fill:"#526d8b"}} />
          <YAxis label={{value:"MW",angle:-90,position:"insideLeft",fontSize:11}} width={67} tick={{fontSize:11}} domain={[0,"auto"]}/>
          <Tooltip formatter={(v,name)=>[v==null?"Not recorded":String(v)+" MW",String(name)+" · indicative"]} />
          <Legend verticalAlign="top" height={34}/>
          <Bar dataKey="production" name="Production" fill="#0758b8" radius={[4,4,0,0]} isAnimationActive={false}/>
          <Bar dataKey="consumption" name="Consumption" fill="#69b5e8" radius={[4,4,0,0]} isAnimationActive={false}/>
        </BarChart>
      </ResponsiveContainer></div>
      <p className="chart-caption">Unrecorded directions are null, never plotted as zero. These values are conditional operator estimates awaiting independent numerical recheck.</p>
    </div>
    <div className="audit-summary"><strong>Independent source audit</strong>
      <span><b>0 / {observations.length}</b> numerically rechecked</span>
      <span>{observations.length} pending records · original 17 October capture retained unchanged</span>
      <a href="/quality#audit">Audit method →</a>
    </div>
  </section>;
}
