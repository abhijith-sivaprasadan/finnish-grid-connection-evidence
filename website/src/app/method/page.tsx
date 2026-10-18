import type { Metadata } from "next";
import Link from "next/link";
export const metadata:Metadata={title:"Method and limits"};
export default function Method(){return <><section className="page-hero"><div className="wrap">
  <p className="eyebrow">03 / Transparent research method</p><h1>Strong claims need <em>strong evidence.</em></h1>
  <p className="lede">We keep observation, source transcription, modelling and operator confirmation separate. That separation is central to this project.</p>
 </div></section>
 <section className="section"><div className="wrap">
   <div className="section-intro"><p className="eyebrow">Evidence hierarchy</p><h2>What is observed? What is inferred?</h2></div>
   <div className="grid-2">
    <article className="research-card"><span className="kicker">01 · indicative</span><h3>Grid Scope estimate</h3>
      <p>Source-transcribed conditional figures for specific named grid points, connection directions and source years. Original capture time and source link retained. No independent numeric recheck yet.</p></article>
    <article className="research-card"><span className="kicker">02 · measured context</span><h3>National operational intervals</h3>
      <p>Authenticated Fingrid and ENTSO-E feeds stored with exact source-defined timestamps, units and retrieval history. Not a measurement of remaining substation capacity.</p></article>
    <article className="research-card"><span className="kicker">03 · simulated</span><h3>Scenario results</h3>
      <p>Future model outputs must retain assumptions and version identity. The current public atlas does not claim a validated AC load-flow, N-1 network analysis or access to operator network models.</p></article>
    <article className="research-card"><span className="kicker">04 · documentary</span><h3>Operator confirmation</h3>
      <p>Would require a specific, traceable operator document. There are no confirmed available-MW values in the current public source sample.</p></article>
   </div>
 </div></section>
 <section className="section compact"><div className="wrap"><div className="feature-band">
  <div><p className="eyebrow">Critical scientific boundary</p><h2>Do not sum the point capacities.</h2></div>
  <div><p>Connection outcomes are conditional and interdependent. Other projects, reinforcement schedules, system strength and grid protection may affect connectability. Missing values are not zeros; national load minus production is not local headroom.</p></div>
 </div></div></section>
 <section className="section"><div className="wrap"><div className="section-intro">
  <p className="eyebrow">Reproducibility &amp; attribution</p><h2>Open methods. Qualified evidence.</h2></div>
  <div className="source-links">
   <a href="https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/" target="_blank" rel="noreferrer">Fingrid Grid Scope <span>Original indicative source ↗</span></a>
   <a href="https://data.fingrid.fi/" target="_blank" rel="noreferrer">Fingrid Open Data <span>National series · attribution required ↗</span></a>
   <a href="https://transparency.entsoe.eu/" target="_blank" rel="noreferrer">ENTSO-E Transparency <span>Official time series portal ↗</span></a>
   <a href="https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence" target="_blank" rel="noreferrer">GitHub research repository <span>Source code, tests, audits and capture log ↗</span></a>
  </div>
  <p className="footnote">Publishing records through this demonstrator does not mean that every source row has been independently reproduced from the operator's live interface. Check the source and licensing terms before redistributing data.</p>
  <div className="action-row"><Link className="button" href="/connections">Explore observations ↗</Link><Link className="button secondary" href="/api">Use the read-only API ↗</Link></div>
 </div></section></>}
