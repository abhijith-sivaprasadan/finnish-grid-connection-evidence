"use client";
import Link from "next/link";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Operation } from "@/lib/types";
import { FEEDS } from "@/lib/workbench-shared";

const palette=["#3b82f6","#08a7b7","#8678eb"];
export function OverviewTrends({rows}:{rows:Operation[]}){
 const show=FEEDS.map((feed,index)=>({
  ...feed,color:palette[index],
  data:rows.filter(row=>row.source===feed.source&&row.dataset_id===feed.dataset_id).sort((a,b)=>a.timestamp_utc.localeCompare(b.timestamp_utc))
 }));
 return <div className="pulse-panel">
  <div className="panel-heading">
    <div><span className="module-tag">NATIONAL OPERATIONS</span><h2>System pulse</h2><p>Most recently stored UTC day · historical source records</p></div>
    <Link className="panel-action" href="/operations?days=2">Open workbench <span aria-hidden="true">↗</span></Link>
  </div>
  <div className="pulse-series">
   {show.map(feed=><div className="pulse-item" key={feed.dataset_id}>
    <div className="pulse-item-header"><span className="pulse-source"><i style={{background:feed.color}}/>{feed.label}</span>
      <span className="pulse-unit">{feed.unit}</span></div>
    {feed.data.length>0?<><div className="pulse-number">
      {feed.data[feed.data.length-1].value.toLocaleString("en-US",{maximumFractionDigits:1})}
      <small>{feed.unit}</small></div>
      <div className="pulse-spark" role="img" aria-label={feed.label+": "+feed.data.length+" observed source intervals"}>
       <ResponsiveContainer width="100%" height={92}>
         <AreaChart data={feed.data.map(p=>({value:p.value,time:Date.parse(p.timestamp_utc)}))} margin={{top:6,bottom:4,left:1,right:1}}>
           <defs><linearGradient id={"pulse"+feed.dataset_id} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={feed.color} stopOpacity=".21"/><stop offset="100%" stopColor={feed.color} stopOpacity="0"/></linearGradient></defs>
           <XAxis hide dataKey="time" type="number" domain={["dataMin","dataMax"]}/>
           <YAxis hide domain={["dataMin - 200","dataMax + 200"]}/>
           <Tooltip labelFormatter={v=>new Date(Number(v)).toISOString().slice(0,16).replace("T"," ")+" UTC"}
             formatter={v=>[Number(v).toLocaleString("en-US",{maximumFractionDigits:2})+" "+feed.unit,"Reported"]}/>
           <Area type="linear" dataKey="value" stroke={feed.color} strokeWidth={2.2} fill={"url(#pulse"+feed.dataset_id+")"} dot={false} isAnimationActive={false} connectNulls={false}/>
         </AreaChart>
       </ResponsiveContainer></div>
      <p className="pulse-last">{feed.data.length} stored historical intervals</p></>:
      <div className="pulse-empty">No stored observations in this day. No synthetic fallback.</div>}
   </div>)}
  </div>
  <div className="panel-footnote">Three independent provider series · units and definitions are not interchangeable. No local connection headroom is inferred.</div>
 </div>;
}
