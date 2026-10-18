"use client";
import { CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, Line, LineChart } from "recharts";
import type { Operation } from "@/lib/types";
export function OperationsChart({rows}:{rows:Operation[]}) {
  const data=[...rows].reverse().map(p=>({
    label:p.timestamp_utc.slice(5,16).replace("T"," "),
    value:p.value,unit:p.unit,date:p.timestamp_utc,
  }));
  if(!data.length) return null;
  return <div role="img" aria-label={"Chart with "+data.length+" reported national operational observations"} className="chart-canvas">
  <ResponsiveContainer width="100%" height={340}>
    <LineChart data={data} margin={{top:14,right:18,left:10,bottom:15}}>
      <CartesianGrid stroke="#e3edf8" strokeDasharray="2 4"/>
      <XAxis dataKey="label" tick={{fontSize:10,fill:"#55708e"}} minTickGap={35}/>
      <YAxis tick={{fontSize:11,fill:"#55708e"}} width={67} domain={["auto","auto"]}/>
      <Tooltip cursor={{stroke:"#9dbfe7",strokeDasharray:"4 4"}} contentStyle={{border:"1px solid #dbe6f2",borderRadius:10,boxShadow:"0 9px 24px #00358014",fontFamily:"DM Sans, sans-serif",fontSize:12}} labelStyle={{color:"#003580",fontWeight:800}} labelFormatter={(_label,payload)=>(payload && payload.length)?String(payload[0].payload.date):""}
        formatter={(value,name,props)=>{
          const number=Number(value); const unit=props.payload?.unit??"";
          return [number.toLocaleString("en-US",{maximumFractionDigits:2})+" "+unit,"Reported value"];
        }}/>
      <Line dataKey="value" type="linear" stroke="#003580" strokeWidth={2.6}
        dot={false} isAnimationActive={false} connectNulls={false}/>
    </LineChart>
  </ResponsiveContainer></div>;
}
