import Link from "next/link";
import { overview, points, coverage } from "@/lib/repository";
import { operationalWindow } from "@/lib/workbench";
import { OverviewTrends } from "@/components/overview-trends";
import type { Operation } from "@/lib/types";

export const dynamic="force-dynamic";
const cleanPoint=(s:string)=>s.replace(/ 400 kV$/,"");
export default async function Home(){
 const result=await Promise.allSettled([
  overview(),points(new URLSearchParams("limit=20")),coverage()
 ]);
 const summary=result[0].status==="fulfilled"?result[0].value:null;
 const nodes=result[1].status==="fulfilled"?result[1].value.data:[];
 const grid=result[2].status==="fulfilled"?result[2].value:null;
 const latest=summary?.newest_operational_interval_utc??null;
 const age=latest?Math.max(0,Math.floor((Date.now()-Date.parse(latest))/3600000)):null;
 let rows:Operation[]=[];
 if(latest&&summary?.data_mode==="neon"){
  try{ rows=(await operationalWindow(latest,1)).data; }catch{ /* No invented chart observations. */ }
 }
 const counts=grid?.coverage;
 const published=counts?.published??null, intersections=counts?.intersections??null;
 const missing=counts?.missing_in_compiled_capture??null;
 const ratio=published!==null&&intersections?Math.round(100*published/intersections):null;
 return <>
  <section className="dashboard-heading">
   <div className="dashboard-kicker"><span className="live-signal-dot"/> WORKSPACE OVERVIEW <span className="kicker-divider">/</span> FINLAND · PUBLIC EVIDENCE</div>
   <div className="dashboard-title-row">
    <div><h1>Electricity grid, <span>understood.</span></h1><p>One research workspace for connection outlooks, national system history and evidence quality. Explore published observations—and exactly where the evidence stops.</p></div>
    <div className="dashboard-header-actions">
     <Link className="button" href="/connections">Explore connections <span aria-hidden="true">↗</span></Link>
     <Link className="button secondary" href="/quality">View data quality</Link>
    </div>
   </div>
  </section>
  <section className="dashboard-info-line" aria-label="Data interpretation and current status">
   <div className="info-main">
    <span className={"info-status-dot"+(summary?.data_mode==="neon"?" good":"")}/>
    <div><strong>{summary?.data_mode==="neon"?"Database connected · read-only":summary?.data_mode==="compiled_snapshot"?"Compiled source snapshot":"Evidence store unavailable"}</strong>
    <span>{latest?"Latest stored historical interval ends "+latest.slice(0,16).replace("T"," ")+" UTC"+(age!==null?" · "+age+" hours old":""):
      "National operational history unavailable; capacity sample may still be shown"}</span></div>
   </div>
   <Link href="/method">Understand the source hierarchy <span aria-hidden="true">→</span></Link>
  </section>
  <section className="dashboard-metrics" aria-label="Coverage of current research sample">
    <div className="dash-metric"><span className="metric-dot blue"/> <p>CONNECTION POINTS</p><strong>{summary?.points??"—"}</strong><small>Selected 400 kV stations</small></div>
    <div className="dash-metric"><span className="metric-dot cyan"/><p>INDICATIVE RECORDS</p><strong>{summary?.capacity_observations??"—"}</strong><small>Original 18 screenshot-matched · indicative only</small></div>
    <div className="dash-metric"><span className="metric-dot violet"/><p>STORED OPERATIONS</p><strong>{summary?.data_mode==="neon"?summary.operational_rows_stored.toLocaleString("en-US"):"—"}</strong><small>Includes retrieval revisions</small></div>
    <div className="dash-metric"><span className="metric-dot amber"/><p>SOURCE FRESHNESS</p><strong>{age!==null?age>=24?Math.floor(age/24)+"d":age+"h":"—"}</strong><small>{latest?"Since latest historical interval":"No interval timestamp"}</small></div>
  </section>
  <div className="dashboard-section-label"><span>ANALYTICAL MODULES</span><span>01 — 03</span></div>
  <div className="dashboard-primary-grid">
   <OverviewTrends rows={rows}/>
   <section className="coverage-panel">
    <div className="panel-heading"><div><span className="module-tag">GRID SCOPE SAMPLE</span><h2>Evidence coverage</h2><p>Recorded year × direction × point combinations</p></div><Link href="/connections" className="panel-action">Details ↗</Link></div>
    <div className="coverage-meter-wrap">
      <div className="coverage-meter" style={{"--coverage":(ratio??0)+"%"} as React.CSSProperties}
         aria-label={ratio===null?"Coverage unavailable":ratio+" percent of selected sample intersections recorded"}>
        <span><strong>{ratio===null?"—":ratio+"%"}</strong><small>RECORDING</small></span>
      </div>
      <div className="coverage-legend">
       <div><i className="legend-dot recorded"/><span>Recorded intersections</span><strong>{published??"—"}</strong></div>
       <div><i className="legend-dot unrecorded"/><span>Not in this capture</span><strong>{missing??"—"}</strong></div>
       <div><i className="legend-dot unaudited"/><span>Original screenshot matches</span><strong>{summary?.source_transcription_screenshot_review.matched??"—"}</strong></div>
      </div>
    </div>
    <div className="panel-footnote">This is <strong>sample recording completeness</strong>, not 60% of Finland's connection capacity. Blank intersections are unknown, not zero.</div>
    <Link href="/quality#audit" className="coverage-audit-link">Review the 18-row screenshot audit <span aria-hidden="true">↗</span></Link>
   </section>
  </div>
  <div className="dashboard-secondary-grid">
   <section className="point-panel">
    <div className="panel-heading"><div><span className="module-tag">CONNECTION EVIDENCE</span><h2>Explore the point index</h2><p>Selected Fingrid 400 kV connection points</p></div><Link href="/connections" className="panel-action">Open matrix ↗</Link></div>
    {nodes.length? <div className="dash-point-list">{nodes.map((point,i)=><Link key={point.connection_point_id} href={"/connections?point_id="+encodeURIComponent(point.connection_point_id)}>
     <span className="point-index">{String(i+1).padStart(2,"0")}</span><span className="point-label"><strong>{cleanPoint(point.name)}</strong><small>Fingrid · {point.voltage_kv??"?"} kV</small></span><span className="point-forward" aria-hidden="true">↗</span>
    </Link>)}</div>:<p className="notice warn">No connection-point catalogue currently available.</p>}
   </section>
   <section className="audit-panel">
    <div className="panel-heading"><div><span className="module-tag">EVIDENCE INTEGRITY</span><h2>What still needs work</h2><p>Visible limitations—not hidden assumptions</p></div></div>
    <div className="audit-step"><span className="audit-step-icon pending">!</span><div><strong>18 indicative source values</strong><p>Original values screenshot-matched; no operator confirmation of actual connectability.</p></div><Link href="/quality#audit" aria-label="Open source audit">↗</Link></div>
    <div className="audit-step"><span className="audit-step-icon pass">✓</span><div><strong>National historical records</strong><p>Authenticated observations stay separate from point-specific capacity.</p></div><Link href="/operations" aria-label="Open national operations">↗</Link></div>
    <div className="audit-step"><span className="audit-step-icon info">i</span><div><strong>Modelled outcomes</strong><p>No operator-confirmed headroom or reconstructed transmission topology.</p></div><Link href="/method" aria-label="Open evidence method">↗</Link></div>
    <Link href="/quality" className="panel-action audit-panel-footer">Explore quality and provenance <span aria-hidden="true">↗</span></Link>
   </section>
  </div>
  <div className="dashboard-bottom-note"><div><strong>Built for scrutiny, not certainty.</strong><span>Source-linked · missing is not zero · conditional estimates cannot be added.</span></div><Link href="/method">Read the evidence rules <span aria-hidden="true">→</span></Link></div>
 </>;
}
