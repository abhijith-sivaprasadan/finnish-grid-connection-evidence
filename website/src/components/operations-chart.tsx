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
      <CartesianGrid stroke="#e6dfcf" strokeDasharray="2 4"/>
      <XAxis dataKey="label" tick={{fontSize:10,fill:"#52685f"}} minTickGap={35}/>
      <YAxis tick={{fontSize:11,fill:"#52685f"}} width={67} domain={["auto","auto"]}/>
      <Tooltip labelFormatter={(_label,payload)=>(payload && payload.length)?String(payload[0].payload.date):""}
        formatter={(value,name,props)=>{
          const number=Number(value); const unit=props.payload?.unit??"";
          return [number.toLocaleString("en-US",{maximumFractionDigits:2})+" "+unit,"Reported value"];
        }}/>
      <Line dataKey="value" type="linear" stroke="#20513d" strokeWidth={2}
        dot={false} isAnimationActive={false} connectNulls={false}/>
    </LineChart>
  </ResponsiveContainer></div>;
}
