import type { Metadata } from "next";
import Link from "next/link";
import { overview } from "@/lib/repository";
import { chooseDays, operationalWindow } from "@/lib/workbench";
import { OperationsWorkbench } from "@/components/operations-workbench";
import type { Operation } from "@/lib/types";
export const dynamic="force-dynamic";
export const metadata:Metadata={title:"National operations workbench"};
type SP=Promise<Record<string,string|string[]|undefined>>;
export default async function Operations({searchParams}:{searchParams:SP}) {
  const params=await searchParams;
  let days:1|2|3|7=3, fault:string|null=null;
  try{days=chooseDays(params.days);}catch{fault="Invalid time window: use 1, 2, 3 or 7 UTC days.";}
  let rows:Operation[]=[];
  let window:{from:string;to:string}|null=null;
  let latest:string|null=null;
  let total:number|null=null;
  if(!fault) try {
    const state=await overview();
    latest=state.newest_operational_interval_utc;
    total=state.operational_rows_stored;
    if(state.data_mode!=="neon"||!latest) throw new Error("EMPTY_DATABASE");
    const result=await operationalWindow(latest,days);
    window=result.window;
    rows=result.data;
  } catch {fault="The read-only source database or requested interval is unavailable. No values were substituted.";}
  const age=latest?Math.floor((Date.now()-Date.parse(latest))/3600000):null;
  const unique=new Set(rows.map(r=>[r.source,r.dataset_id,r.timestamp_utc,r.interval_end_utc].join("|"))).size;
  return <>
    <section className="page-hero"><div className="wrap"><p className="eyebrow">02 / Source-linked operational chronology</p>
      <h1>Systems <em>in time.</em></h1><p className="lede">Explore actual timestamped Finnish consumption, production and load series together—without confusing national data with substation headroom.</p></div></section>
    <section className="section compact"><div className="wrap">
      <div className="wb-topnav"><p className="eyebrow">SELECT WINDOW · MOST RECENT STORED INTERVAL</p>
        <nav className="wb-range" aria-label="UTC range">
          {[1,2,3,7].map(n=><Link key={n} href={"/operations?days="+n} className={!fault&&days===n?"active":""}>{n} day{n>1?"s":""}</Link>)}
        </nav>
      </div>
      {fault&&<p role="alert" className="notice warn">{fault}</p>}
      {window&&<div className="wb-period"><strong>{window.from.slice(0,10)} — {window.to.slice(0,10)} UTC</strong>
        <span>Anchored to latest stored UTC day, not necessarily today · {unique} distinct intervals across sources</span></div>}
      {age!==null&&age>120&&<p role="status" className="notice warn">The latest stored source interval is {age} hours old. Historical records only; not live telemetry.</p>}
      {rows.length>0?<OperationsWorkbench rows={rows}/>:!fault&&<p className="notice">No intervals in the selected window. There is no interpolated replacement.</p>}
      <div className="wb-summary-row"><span>Raw stored rows (including retrieval revisions): <strong>{total??"—"}</strong></span>
        <span>Distinct intervals in selected window: <strong>{unique}</strong></span><Link href="/quality">Inspect source coverage and revisions ↗</Link></div>
      <div className="limit-box"><span className="kicker">Research boundary</span><p>Fingrid and ENTSO-E publish national measurements with different definitions and units. Side-by-side inspection does not establish that their levels are equivalent, nor available connection capacity. The export preserves the original units, retrieval times, intervals and source URLs.</p></div>
    </div></section>
  </>;
}
