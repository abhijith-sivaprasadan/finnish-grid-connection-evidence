"use client";
import { useMemo } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { FEEDS } from "@/lib/workbench-shared";
import type { Operation } from "@/lib/types";

function quoteCsv(input:unknown) {
  const s=String(input??"");return /[",\r\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;
}
function downloadCsv(rows:Operation[]) {
  const fields=["source","dataset_id","metric","timestamp_utc","interval_end_utc","value","unit","area","retrieved_at","source_url"] as const;
  const text=[fields.join(","),...rows.map(row=>fields.map(field=>quoteCsv(row[field])).join(","))].join("\r\n")+"\r\n";
  const blob=new Blob([text],{type:"text/csv;charset=utf-8"});
  const url=URL.createObjectURL(blob);
  const link=document.createElement("a");link.href=url;link.download="finnish-grid-national-operations-source-intervals.csv";
  document.body.append(link);link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),3000);
}
const colours=["#064caa","#349add","#0c8091"];
export function OperationsWorkbench({rows}:{rows:Operation[]}) {
  const series=useMemo(()=>FEEDS.map((f,i)=>{
    const vals=rows.filter(r=>r.source===f.source&&r.dataset_id===f.dataset_id)
      .sort((a,b)=>a.timestamp_utc.localeCompare(b.timestamp_utc));
    return {...f,color:colours[i],rows:vals};
  }),[rows]);
  return <div className="workbench" aria-label="Synchronized operational measurements">
    <div className="wb-heading">
      <div><p className="eyebrow">THREE SOURCE-LINKED SERIES / 02</p>
        <h2>National operations, aligned in UTC.</h2>
        <p>Hover across the three aligned panels to inspect the same time position. Different operator definitions and units are deliberately not combined on one axis.</p></div>
      <button className="button secondary" type="button" onClick={()=>downloadCsv(rows)} disabled={rows.length===0}>
        Export {rows.length.toLocaleString("en-US")} source intervals ↓
      </button>
    </div>
    {series.map(feed=><section className="wb-chart-row" key={feed.source+feed.dataset_id}>
      <div className="wb-chart-title">
        <div><p className="eyebrow">{feed.source.toUpperCase()} · DATASET {feed.dataset_id}</p><h3>{feed.label}</h3></div>
        <span className="wb-pill">{feed.rows.length.toLocaleString("en-US")} intervals · {feed.unit}</span>
      </div>
      {feed.rows.length>0?<div className="wb-chart" role="img" aria-label={feed.label+": "+feed.rows.length+" source-reported historical UTC intervals"}>
        <ResponsiveContainer width="100%" height={225}>
          <LineChart data={feed.rows.map(r=>({...r,time:Date.parse(r.timestamp_utc)}))}
            syncId="finnish-atlas-utc" syncMethod="value"
            margin={{top:10,right:25,left:2,bottom:0}}>
            <CartesianGrid stroke="#e6edf6" strokeDasharray="2 4"/>
            <XAxis dataKey="time" type="number" domain={["dataMin","dataMax"]} tickCount={5}
              tickFormatter={v=>new Date(v).toISOString().slice(5,16).replace("T"," ")}
              tick={{fontSize:10,fill:"#55708e"}}/>
            <YAxis width={71} tick={{fontSize:11,fill:"#55708e"}} domain={["auto","auto"]}/>
            <Tooltip labelFormatter={v=>new Date(Number(v)).toISOString().replace("T"," ").slice(0,16)+" UTC"}
              formatter={v=>[Number(v).toLocaleString("en-US",{maximumFractionDigits:2})+" "+feed.unit,"Reported value"]}
              contentStyle={{fontSize:12,borderRadius:12,border:"1px solid #d6e5f3"}}/>
            <Line type="linear" dataKey="value" stroke={feed.color} strokeWidth={2}
              dot={false} connectNulls={false} isAnimationActive={false}/>
          </LineChart>
        </ResponsiveContainer>
      </div>:<p className="notice">No source measurements for this feed in the selected period. This is a data gap, not a zero series.</p>}
      <div className="wb-series-meta"><span>Last interval: {feed.rows.length?feed.rows[feed.rows.length-1].interval_end_utc.replace("T"," ").slice(0,16)+" UTC":"—"}</span>
        <a href={feed.rows[0]?.source_url||"https://data.fingrid.fi/"} rel="noreferrer" target="_blank">Original source ↗</a></div>
    </section>)}
    <p className="chart-caption">Not an implied Fingrid/ENTSO-E reconciliation: MWh/h and MW report different published metric definitions. No generation minus load series is interpreted as a connection-capacity surplus. Missing intervals are never interpolated.</p>
  </div>;
}
