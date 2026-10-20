import type { Metadata } from "next";
import Link from "next/link";
import archive from "@/lib/fingrid-archive-coverage-2025.json";
import winter from "@/lib/pypsa-long-winter-2025.json";
import model from "@/lib/pypsa-scenario-results.json";

export const metadata:Metadata={
 title:"Grid analyst portfolio case study",
 description:"An independently developed Finnish grid-data and indicative power-availability screener: source-reviewed substations, operator national series, auditable data storage and explicitly hypothetical PyPSA sensitivity."
};

const evidence=[
 {n:"01",title:"Own the grid data",detail:"Authenticated Fingrid consumption/production (datasets 124/74) and ENTSO-E A65 load are ingested as dated national operational intervals, keeping source units, retrieval revisions and integrity checks.",href:"/operations",link:"Explore real time-series evidence"},
 {n:"02",title:"Understand current and future availability",detail:"Five selected Fingrid Grid Scope points and 18 reviewed indicative observations are recorded separately by direction and published effective year. Missing combinations are unknown, not zero.",href:"/connections",link:"Inspect point-year evidence"},
 {n:"03",title:"Screen candidate requests",detail:"A 100 MW / 2030 example classifies exact-year source thresholds, uncertain or absent records and unit mismatches. It does not approve or rank physically connectable sites.",href:"/screening?demand_mw=100&year=2030&direction=consumption&voltage=all",link:"Run the 100 MW evidence screen"},
 {n:"04",title:"Model and communicate uncertainty",detail:"Source-anchored PyPSA studies of national operating stress, two 27-day winters, and market-corridor assumptions are clearly separated from point capacity. No verified AC/N-1 or site headroom model is implied.",href:"/analysis",link:"Inspect sensitivity and provenance"}
];

export default function CaseStudy(){
 return <>
  <section className="page-hero"><div className="wrap">
   <p className="eyebrow">Portfolio / energy & grids / independent case study</p>
   <h1>From grid data to <em>decision evidence.</em></h1>
   <p className="lede">A Finland-focused proof of concept built around the deliverables of a Grid Analyst role: source stewardship, conditional capacity outlooks, operational context, and clearly qualified model scenarios. This is personal research, not a Krios or Fingrid production system. An independently audited Netherlands capacity-map source pilot is linked separately, without comparing congestion categories to Finnish MW.</p>
   <div className="action-row"><Link className="button" href="/screening?demand_mw=100&year=2030&direction=consumption&voltage=all">Start with a 100 MW screening request ↗</Link><Link className="button secondary" href="/connections">Inspect published estimates ↗</Link></div>
  </div></section>
  <section className="section compact"><div className="wrap">
   <div className="data-strip three">
    <div><strong>5</strong><span>Selected Grid Scope connection points</span></div>
    <div><strong>18 / 18</strong><span>Original capacity readings matched to reviewer-supplied screenshots</span></div>
    <div><strong>{archive.verified_complete_days}</strong><span>Complete UTC days of authentic 2025 Fingrid pairs in a partial archive</span></div>
   </div>
   <p className="footnote">Counts measure captured evidence, not the number of available grid sites. The 18 screenshot matches check transcription only; they are not operator-approved capacity. The 2025 archive is incomplete, with {archive.known_missing_source_days} source-gap dates and {archive.not_covered_by_archives_days} dates not covered by its collected files.</p>
  </div></section>
  <section className="section"><div className="wrap">
   <div className="section-intro"><p className="eyebrow">Role-specific capability mapping</p><h2>Four activities. Four reproducible outputs.</h2><p>Every claim links to a working analysis or dated source audit.</p></div>
   <div className="grid-2">{evidence.map(e=><article className="research-card" key={e.n}>
     <span className="kicker">{e.n} / role deliverable</span><h3>{e.title}</h3><p>{e.detail}</p><Link href={e.href}>{e.link} ↗</Link>
   </article>)}</div>
  </div></section>
  <section className="section compact"><div className="wrap">
   <div className="feature-band"><div><p className="eyebrow">A worked decision, not a site recommendation</p><h2>100 MW consumption in 2030.</h2></div>
    <div><p>For the five-point October 2026 Grid Scope capture, Seinäjoki and Uusnivala each had a screenshot-reviewed <strong>400 MW indicative 2030 consumption estimate</strong>. The other three had no corresponding figure in this capture. An indicative threshold match only authorises a closer look: the operator must still evaluate project location, timing, power factor, load profile, queues, contingencies and reinforcement plans.</p>
      <Link href="/screening?demand_mw=100&year=2030&direction=consumption&voltage=all">Open auditable screening classifications →</Link>
    </div>
   </div>
  </div></section>
  <section className="section"><div className="wrap">
   <div className="section-intro"><p className="eyebrow">Research extension / evidence limits</p><h2>Models are a separate tier.</h2><p>The source-reviewed capacity matrix remains the primary signal; model stress metrics are never substituted into a substation's published MW field.</p></div>
   <div className="grid-2">
    <article className="research-card"><span className="kicker">National 2026 · one bus</span><h3>{model.scenarios.length} solver-verified cases</h3>
     <p>Two measured October 2026 UTC days, a fictional 100 MW additional load, assumed 1,500 MW balancing support and optional flexible load or battery. A solver-defined slack is not a historic Finnish outage or available connection capacity.</p><Link href="/analysis">View 48-hour PyPSA study ↗</Link></article>
    <article className="research-card"><span className="kicker">Winter 2025 · historical partial coverage</span><h3>{winter.scenario_count_all_caps} project optimizations + {winter.baseline_count} baselines</h3>
     <p>Two separate uninterrupted 27-day winters, assumptions varied in the historical optimisation. Sweden-border market constraints use commercial trade data, not AC branch thermal ratings.</p><Link href="/analysis/borders-2025">View winter research ↗</Link></article>
   </div>
   <div className="limit-box"><span className="kicker">Explicit stop line</span>
     <p>The licensed 2024 OSM-derived 220/400 kV proxy and a February 2025 third-party map strongly overlap geographically. Neither validates a 2025 Fingrid as-built network, actual impedance/thermal constraints, real electrical N−1 compliance or a site's connection rights. The February map has no explicit redistribution grant, so raw third-party geometry is not published. An operator-confirmed capacity count of <strong>zero</strong> is intentional.</p>
   </div>
  </div></section>
  <section className="section"><div className="wrap">
   <div className="section-intro"><p className="eyebrow">Reproducibility and transparency</p><h2>Review the source and the limitations.</h2></div>
   <div className="source-links">
    <Link href="/engineering">Independent electrical engineering lab <span>CIGRE HV/MV nonlinear AC, N−1, PyPSA parity and regional v2 →</span></Link>
    <Link href="/network-map">Interactive 2024 OSM proxy geography <span>104 high-voltage AC source nodes; not the five named Grid Scope points →</span></Link>
    <Link href="/netherlands">Netherlands official congestion-data pilot <span>Source-verified 896 records, metadata only →</span></Link>
    <a href="https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence" target="_blank" rel="noreferrer">Source repository <span>Python / Next.js / SQLite / Neon / tests ↗</span></a>
    <a href="https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/blob/main/docs/KRIOS_DEMO.md" target="_blank" rel="noreferrer">Short interview demonstration <span>Source observations, screening and models ↗</span></a>
    <a href="https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/blob/main/docs/STATUS.md" target="_blank" rel="noreferrer">Dated release status <span>What works, what is not independently verified ↗</span></a>
    <a href="https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/" target="_blank" rel="noreferrer">Original Fingrid Grid Scope <span>Indicative operator viewer and disclaimers ↗</span></a>
   </div>
  </div></section>
 </>;
}
