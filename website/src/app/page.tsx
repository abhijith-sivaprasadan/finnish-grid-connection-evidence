import Link from "next/link";
import { overview, coverage } from "@/lib/repository";
import { evidenceCatalogue } from "@/lib/catalogue";
import { operationalWindow } from "@/lib/workbench";
import { OverviewTrends } from "@/components/overview-trends";
import type { Capacity,Operation,Point } from "@/lib/types";
import { sourceReviewStatus } from "@/lib/verification";

export const dynamic="force-dynamic";
const short=(name:string)=>name.replace(/\s+\d+\s*kV$/i,"");
export default async function Home(){
 const results=await Promise.allSettled([overview(),evidenceCatalogue(),coverage()]);
 const summary=results[0].status==="fulfilled"?results[0].value:null;
 const stations:Point[]=results[1].status==="fulfilled"?results[1].value.stations:[];
 const capacity:Capacity[]=results[1].status==="fulfilled"?results[1].value.observations:[];
 const counts=results[2].status==="fulfilled"?results[2].value.coverage:null;
 const latest=summary?.newest_operational_interval_utc??null;
 const age=latest?Math.max(0,Math.floor((Date.now()-Date.parse(latest))/3600000)):null;
 let operations:Operation[]=[];
 if(latest&&summary?.data_mode==="neon")try{operations=(await operationalWindow(latest,1)).data;}catch{}
 const year=capacity.map(c=>c.effective_year).filter((x):x is number=>x!==null).sort((a,b)=>a-b)[0]??null;
 const byCell=new Map<string,Capacity[]>();
 for(const row of capacity){const k=[row.connection_point_id,row.direction,row.effective_year].join("|");byCell.set(k,[...(byCell.get(k)||[]),row]);}
 const reading=(p:Point,d:"production"|"consumption")=>year===null?[]:byCell.get([p.connection_point_id,d,year].join("|"))??[];
 const recorded=counts?.published??0, gaps=counts?.missing_in_compiled_capture??0;
 const screenshotMatches=capacity.filter(c=>sourceReviewStatus(c).status==="screenshot_match").length;
 return <div className="df-home">
   <header className="df-home-header">
    <div><p className="df-overline">FINLAND / PUBLIC GRID EVIDENCE</p><h1>Grid connection evidence</h1><p>Inspect the available source records before drawing conclusions. Five original stations are a research sample—not Finland's full network.</p></div>
    <div className="df-header-actions"><Link href="/screening" className="button">Screen a 100 MW connection ↗</Link> <Link href="/connections">Source matrix →</Link></div>
   </header>
   <div className="dashboard-archive-link"><div><strong>Historical main-grid station archive</strong><span>128 source-listed rows · printed 127 · table heading 1.1.2020 · not a current capacity register</span></div><Link href="/stations">Explore source names ↗</Link></div>
   <div className="dashboard-archive-link"><div><strong>NEW · PyPSA Finland historical demand sensitivity</strong><span>192 real source intervals · 4 HiGHS-optimal scenarios · hypothetical 1,500 MW balancing cap, not grid availability</span></div><Link href="/analysis">Explore system model ↗</Link></div>
   <section className="df-home-stats" aria-label="Recorded data summary">
    <div><span>Substations in this dataset</span><strong>{summary?.points??"—"}</strong><small>Not a national catalogue</small></div>
    <div><span>Recorded indicative values</span><strong>{summary?.capacity_observations??"—"}</strong><small>Dated Fingrid transcriptions</small></div>
    <div><span>Not captured in sample</span><strong>{counts?.missing_in_compiled_capture??"—"}</strong><small>Unknown, not zero MW</small></div>
    <div><span>Screenshot comparison</span><strong>{screenshotMatches}<small> / {capacity.length}</small></strong><small>Transcription only · not network validation</small></div>
   </section>
   <div className="df-home-main">
    <section className="df-home-panel">
     <div className="df-panel-head"><div><p className="df-overline">01 / CONNECTION CAPACITY SOURCE RECORDS</p><h2>What was actually recorded</h2><p>Individually recorded indicative values for {year??"the available"} effective year; showing up to 15 of {stations.length} stations here. Inspect the explorer for all catalogue records.</p></div><Link href="/connections">Inspect all years ↗</Link></div>
     <div className="df-table-scroll" role="region" tabIndex={0} aria-label="Recorded source capacity values by station">
      <table className="df-home-table"><thead><tr><th scope="col">Substation</th><th scope="col">Production · {year??"—"}</th><th scope="col">Consumption · {year??"—"}</th><th scope="col">Open</th></tr></thead><tbody>
      {stations.slice(0,15).map(p=><tr key={p.connection_point_id}><th scope="row"><strong>{short(p.name)}</strong><small>{p.voltage_kv??"—"} kV</small></th>
      {(["production","consumption"] as const).map(d=>{const list=reading(p,d);return <td key={d}>{list.length===1?<><strong>{list[0].capacity_value} {list[0].capacity_unit}</strong><small>Indicative · source capture</small></>:<span className="df-not-captured">{list.length>1?"Needs reconciliation":"Not captured"}</span>}</td>;})}
      <td><Link href={"/connections?point_id="+encodeURIComponent(p.connection_point_id)}>Inspect ↗</Link></td></tr>)}
      </tbody></table>{stations.length===0&&<p className="df-empty">The source catalogue is currently unavailable. No data has been substituted.</p>}</div>
     <footer className="df-panel-footer"><span>{recorded} recorded / {gaps} uncaptured intersections in the selected capture matrix. Not a percentage of Finnish substations.</span><a href="https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/" rel="noreferrer" target="_blank">Fingrid Grid Scope ↗</a></footer>
    </section>
    <aside className="df-home-aside">
     <div className="df-aside-card"><p className="df-overline">EVIDENCE CLASSIFICATION</p><h3>What you can conclude</h3>
      <div className="df-class-row"><strong>Source figures</strong><span>{screenshotMatches} screenshot-matched original records</span></div>
      <div className="df-class-row"><strong>Source coverage</strong><span>{stations.length} sampled connection points only</span></div>
      <div className="df-class-row"><strong>Physical grid headroom</strong><span>Not established</span></div>
      <div className="df-class-row"><strong>Guaranteed connectability</strong><span>Not established</span></div>
      <Link href="/quality#audit">Review the audit →</Link>
     </div>
     <div className="df-aside-card compact"><p className="df-overline">OPERATIONS FRESHNESS</p><h3>{age!==null?age>=24?Math.floor(age/24)+" days old":age+" hours old":"Unavailable"}</h3>
      <p>Latest historical national interval: {latest?latest.slice(0,16).replace("T"," ")+" UTC":"not recorded"}.</p>
      <p>{summary?.data_mode==="neon"?"Read-only source database connected.":summary?.data_mode==="compiled_snapshot"?"Compiled source snapshot mode.":"Evidence store unavailable."}</p>
      <Link href="/operations">Examine national operations →</Link></div>
    </aside>
   </div>
   <section className="df-operations-section"><div className="df-panel-head"><div><p className="df-overline">02 / NATIONAL SYSTEM CONTEXT</p><h2>Separate national operations</h2><p>Historical source series complement the evidence dataset, but do not establish substation-specific capacity.</p></div><Link href="/operations">All intervals ↗</Link></div><OverviewTrends rows={operations}/></section>
   <section className="df-roadmap-note"><h2>Why not every substation?</h2><p>The catalogue currently reflects a deliberately limited, manually transcribed and screenshot-reviewed capture. Fingrid's map shows broader infrastructure, but not every station has a published capacity calculation. A larger inventory must distinguish registered stations, stations with source observations, and stations still awaiting review.</p><Link href="/method">Read source limitations →</Link></section>
  </div>;
}
