import type { Metadata } from "next";
import { operations } from "@/lib/repository";
import { OperationsChart } from "@/components/operations-chart";
export const dynamic="force-dynamic";
export const metadata:Metadata={title:"National operations"};
type SP=Promise<Record<string,string|string[]|undefined>>;
const FEEDS=[
  {label:"Fingrid · Consumption 124",source:"fingrid",dataset_id:"124"},
  {label:"Fingrid · Production 74",source:"fingrid",dataset_id:"74"},
  {label:"ENTSO-E · Actual load A65",source:"entsoe",dataset_id:"A65"},
] as const;
export default async function Operations({searchParams}:{searchParams:SP}){
 const input=await searchParams;
 const requested=FEEDS.find(f=>f.dataset_id===input.dataset_id)??FEEDS[0];
 const q=new URLSearchParams({source:requested.source,dataset_id:requested.dataset_id,limit:"500"});
 let data:Awaited<ReturnType<typeof operations>>|null=null;
 try {data=await operations(q);}catch{ /* No fabricated fallback: show explicit state. */ }
 const rows=data?.data??[];
 const latest=rows[0]?.interval_end_utc;
 const hours=latest?Math.floor((Date.now()-Date.parse(latest))/3600000):null;
 return <><section className="page-hero"><div className="wrap"><p className="eyebrow">02 / National operational chronology</p>
   <h1>The Finnish grid <em>in time.</em></h1><p className="lede">Published consumption, production and load series.
   The original interval timestamps and units are preserved; these do not imply substation headroom.</p></div></section>
   <section className="section compact"><div className="wrap">
   <nav className="feed-links" aria-label="National operational series">
     {FEEDS.map(f=><a className={requested.dataset_id===f.dataset_id?"active":""}
       key={f.dataset_id} href={"/operations?dataset_id="+f.dataset_id}>{f.label}</a>)}
   </nav>
   {data ? <>
     <div className="data-strip three">
       <div><strong>{data.pagination.total}</strong><span>Stored intervals in selected 14-day window</span></div>
       <div><strong>{rows.length?rows[0].unit:"—"}</strong><span>Original provider measurement unit</span></div>
       <div><strong>{hours===null?"—":Math.max(0,hours)+" h"}</strong><span>Latest interval age · UTC</span></div>
     </div>
     {hours!==null&&hours>120&&<p role="status" className="notice warn">Latest operational interval is more than 5 days old. Data should not be described as live telemetry.</p>}
     {rows.length ? <><div className="chart-panel"><p className="eyebrow">Measured national context · UTC</p>
        <h2>{requested.label}</h2><OperationsChart rows={rows}/><p className="chart-caption">Intervals use source-reported start timestamps. Plot is historical context; no interpolation to substation capacity.</p></div>
        <div className="section-intro table-heading"><p className="eyebrow">Provenance</p><h2>Interval-by-interval records.</h2></div>
        <div className="table-wrap"><table><thead><tr><th>Start (UTC)</th><th>End (UTC)</th><th>Value</th><th>Retrieved (UTC)</th><th>Original source</th></tr></thead><tbody>
        {rows.slice(0,80).map((r,i)=><tr key={r.timestamp_utc+r.dataset_id+i}><td>{r.timestamp_utc.slice(0,16).replace("T"," ")}</td><td>{r.interval_end_utc.slice(0,16).replace("T"," ")}</td>
        <td className="value-cell">{r.value.toLocaleString("en-US",{maximumFractionDigits:2})} {r.unit}</td><td>{r.retrieved_at.slice(0,16).replace("T"," ")}</td>
        <td><a target="_blank" rel="noreferrer" href={r.source_url}>View source ↗</a></td></tr>)}</tbody></table></div>
        <p className="footnote">Showing up to 80 table rows and 500 chart intervals for performance. For paginated records and other date windows use the <a href="/api">REST API</a>.</p>
      </> : <p className="notice">No source observations found in the most recent 14-day window. No synthetic or filler data are displayed.</p>}
   </>:<p role="alert" className="notice warn">National operations are not available from the public capacity snapshot. The read-only Neon evidence store must be configured before time-series measurements can be shown.</p>}
   <div className="limit-box"><span className="kicker">Data-use boundary</span><p>
     Fingrid Open Data and ENTSO-E are national/bidding-zone context sources; none
     of their totals can validate physical connection capacity at an individual Fingrid substation.</p></div>
   </div></section></>;
}
