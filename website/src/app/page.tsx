import Link from "next/link";
import {overview} from "@/lib/repository";
import {evidenceCatalogue} from "@/lib/catalogue";
import {operationalWindow} from "@/lib/workbench";
import {OverviewTrends} from "@/components/overview-trends";
import {EvidenceMatrix} from "@/components/evidence-matrix";
import {parseScreening,screenRecords} from "@/lib/screening";
import {sourceReviewStatus} from "@/lib/verification";
import type {Capacity,Operation,Point} from "@/lib/types";

export const dynamic="force-dynamic";
export default async function Home(){
 const results=await Promise.allSettled([overview(),evidenceCatalogue()]);
 const summary=results[0].status==="fulfilled"?results[0].value:null;
 const catalogue=results[1].status==="fulfilled"?results[1].value:null;
 const points:Point[]=catalogue?.stations??[];
 const capacities:Capacity[]=catalogue?.observations??[];
 const totalCells=points.length*[...new Set(capacities.map(r=>r.effective_year).filter(y=>y!==null))].length*2;
 const reviewed=capacities.filter(row=>sourceReviewStatus(row).status==="screenshot_match").length;
 const screen=catalogue&&points.length>0?screenRecords(points,capacities,parseScreening(new URLSearchParams("demand_mw=100&year=2030&direction=consumption&connection_type=switchyard"))):null;
 const latest=summary?.newest_operational_interval_utc??null;
 const age=latest?Math.max(0,Math.floor((Date.now()-Date.parse(latest))/3600000)):null;
 let operations:Operation[]=[];
 if(latest&&summary?.data_mode==="neon")try{operations=(await operationalWindow(latest,1)).data;}catch{ /* Show a genuine empty source state. */ }
 return <div className="mvp-home">
  <header className="mvp-hero">
   <div className="mvp-hero-content">
    <p className="df-overline">Finland · Grid evidence &amp; engineering</p>
    <h1>From grid evidence to <em>the next decision.</em></h1>
    <p className="mvp-hero-lead">Explore an indicative 100 MW demand request, trace the published source figures, and see which engineering questions remain open.</p>
    <div className="mvp-hero-actions">
     <Link className="button" href="/screening?demand_mw=100&year=2030&connection_type=switchyard">Explore the 100 MW case <span aria-hidden="true">↗</span></Link>
     <Link className="mvp-hero-text-link" href="/case-study">How the analysis works →</Link>
    </div>
    <p className="mvp-hero-qualification">Independent demonstration using a five-point Fingrid Grid Scope sample. Not an operator connection offer.</p>
   </div>
   <aside className="mvp-hero-result" aria-label="Illustrative 2030 screening result">
    <span className="mvp-hero-eyebrow">Illustrative request · 2030</span>
    <strong className="mvp-hero-big">100 <small>MW</small></strong>
    <span className="mvp-hero-result-title">Demand · indicative screening</span>
    {screen?<div className="mvp-hero-findings">
      <div><strong>{screen.summary.indicative_threshold_met}</strong><span>Published thresholds met</span></div>
      <div><strong>{screen.summary.unknown_not_captured}</strong><span>Requested-year values missing</span></div>
      <div><strong>{screen.summary.operator_confirmed_feasible}</strong><span>Operator-confirmed connection offers</span></div>
     </div>:<p className="mvp-hero-empty">The source evidence is unavailable. No outcome has been substituted.</p>}
    <Link href="/screening?demand_mw=100&year=2030&connection_type=switchyard">Review results and connection pathway →</Link>
   </aside>
  </header>

  <section className="mvp-flow" aria-label="Explore the evidence workflow">
   <Link href="/screening"><span>01 / Assess</span><strong>Screen a request</strong><small>Choose MW, year and connection arrangement</small><b aria-hidden="true">↗</b></Link>
   <Link href="/connections"><span>02 / Verify</span><strong>Inspect the evidence</strong><small>See captured values, unknowns and source dates</small><b aria-hidden="true">↗</b></Link>
   <Link href="/engineering"><span>03 / Test</span><strong>Examine electrical effects</strong><small>Explore separate benchmark AC and PyPSA studies</small><b aria-hidden="true">↗</b></Link>
  </section>

  <section className="mvp-kpis" aria-label="Scope of source evidence">
   <div><span>Original sampled grid points</span><strong>{catalogue?points.length:"—"}</strong><small>400 kV-labelled sources in this sample</small></div>
   <div><span>Indicative MW records</span><strong>{catalogue?capacities.length:"—"}</strong><small>Captured 17 October 2026</small></div>
   <div><span>Uncaptured sample cells</span><strong>{catalogue?Math.max(0,totalCells-capacities.length):"—"}</strong><small>Unknown, never treated as zero</small></div>
   <div><span>Screenshot transcription reviews</span><strong>{catalogue?reviewed+" / "+capacities.length:"—"}</strong><small>Not physical network validation</small></div>
  </section>

  <section className="mvp-main-grid">
   <div className="mvp-matrix-panel">
    <EvidenceMatrix points={points} observations={capacities}/>
   </div>
   <aside className="mvp-context" aria-label="Data interpretation">
    <div className="mvp-context-card">
     <p className="df-overline">How to interpret</p><h2>A lead is not a connection.</h2>
     <p>Fingrid's Grid Scope values are indicative. Matching a requested MW number does not identify a suitable voltage arrangement, physical headroom, queue position or reinforcement.</p>
     <Link href="/screening">See pathway checks →</Link>
    </div>
    <div className="mvp-context-card compact">
     <p className="df-overline">Location and network context</p><h2>Explore the source topology</h2>
     <p>The interactive 2024 OSM-derived map shows virtual AC nodes and links; the five named Grid Scope points have <strong>not</strong> been matched to these nodes.</p>
     <Link href="/network-map">Open the network map ↗</Link>
    </div>
   </aside>
  </section>

  <section className="mvp-operations df-operations-section">
   <div className="df-panel-head"><div><p className="df-overline">Separate evidence · historical system operations</p>
    <h2>National electricity, not local capacity</h2>
    <p>Fingrid and ENTSO-E source series from the most recently stored UTC day. Different definitions and units remain separate.</p>
   </div><Link href="/operations">Explore time series ↗</Link></div>
   <OverviewTrends rows={operations}/>
   <div className="mvp-operations-meta">Latest source interval: {latest?latest.replace("T"," ").slice(0,16)+" UTC":"unavailable"}{age!==null?" · "+(age>=24?Math.floor(age/24)+" days":age+" hours")+" old":""} · Historical observations only.</div>
  </section>

  <section className="mvp-next">
   <div><span className="df-overline">For deeper technical review</span><h2>Run the model. Keep its assumptions visible.</h2>
    <p>Reference CIGRE AC and N−1 cases, regional PyPSA scenarios and an ODbL-source geographic view. Model outputs do not overwrite the published station evidence.</p>
   </div>
   <div className="mvp-next-actions"><Link className="button" href="/engineering">Explore engineering studies ↗</Link><Link href="/quality">Data quality and provenance →</Link></div>
  </section>
  <footer className="mvp-home-note">Five source points ≠ Finnish national coverage. Neither a published threshold nor a benchmark model establishes operator-approved connection capacity. <Link href="/method">Method and evidence definitions ↗</Link></footer>
 </div>;
}
