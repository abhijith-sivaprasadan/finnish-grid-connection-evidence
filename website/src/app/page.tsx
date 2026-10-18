import Link from "next/link";
import { overview, points } from "@/lib/repository";
export const dynamic="force-dynamic";

export default async function Home() {
  const result = await Promise.allSettled([overview(),points(new URLSearchParams("limit=5"))]);
  const summary = result[0].status==="fulfilled" ? result[0].value : null;
  const nodes = result[1].status==="fulfilled" ? result[1].value.data : [];
  const latest=summary?.newest_operational_interval_utc;
  const age=latest ? Math.floor((Date.now()-Date.parse(latest))/3600000) : null;
  return <>
    <section className="hero"><div className="wrap hero-grid">
      <div>
        <p className="eyebrow">Finnish transmission grid · research demonstrator</p>
        <h1>Where can the grid <em>potentially connect?</em></h1>
        <p className="lede">An evidence-first atlas of indicative substation connection estimates
        and Finland-wide electricity operation. What is recorded, what is conditional,
        and what public data cannot establish.</p>
        <div className="action-row"><Link className="button" href="/connections">Explore connection evidence <span aria-hidden>↗</span></Link>
          <Link className="button secondary" href="/method">Validation &amp; limits</Link></div>
        <p className="hero-note">Not an operator service · No reservations, connection guarantees or unpublished capacity estimates.</p>
      </div>
      <aside className="hero-card"><span className="small-label">Research question</span>
        <h2>How much do published estimates actually tell us?</h2>
        <p>Reported capacity is a conditional screening signal. Connection feasibility
          depends on grid studies, other applicants and network development—not a
          numerical difference between national production and demand.</p>
        <Link href="/method" className="text-link">Understand the claim boundary ↗</Link>
      </aside>
    </div></section>

    <section className="section compact"><div className="wrap">
      {!summary&&<div className="notice warn" role="status">Live evidence store is temporarily unavailable. Counts are not replaced with invented values.</div>}
      {summary?.data_mode==="compiled_snapshot"&&<div className="notice warn" role="status">Displaying the public, source-transcribed 17 October 2026 capacity snapshot. These estimates are not independently operator-rechecked; operational data require the live database. This is not a live Grid Scope feed.</div>}
      <div className="data-strip" aria-label="Evidence stored">
        <div><strong>{summary?.points??"—"}</strong><span>Named 400 kV connection points</span></div>
        <div><strong>{summary?.capacity_observations??"—"}</strong><span>Source-transcribed indicative estimates</span></div>
        <div><strong>{summary?.data_mode==="compiled_snapshot"?"—":summary?.operational_rows_stored??"—"}</strong><span>Historical operational records in connected database</span></div>
        <div><strong>{age===null?"—":Math.max(age,0)+" h"}</strong><span>Age of newest national interval · UTC</span></div>
      </div>
      {age!==null&&age>120&&<p className="notice warn">Operational observations are more than five days old; these are not current live measurements.</p>}
    </div></section>

    <section className="section"><div className="wrap">
      <div className="section-intro"><p className="eyebrow">Read the evidence correctly</p>
        <h2>Two distinct datasets.<br/><em>Two very different claims.</em></h2>
        <p>The atlas deliberately prevents source records from being interpreted as stronger evidence than they support.</p></div>
      <div className="grid-2">
        <article className="research-card"><span className="kicker">01 · Grid Scope</span>
          <h3>Published connection outlook</h3><p>Reported estimates at named substations,
          split by production versus consumption and by the year actually shown in the source.</p>
          <div className="pill note">Source recheck pending</div>
          <Link href="/connections">Explore source observations ↗</Link></article>
        <article className="research-card"><span className="kicker">02 · National operating conditions</span>
          <h3>Fingrid + ENTSO-E chronology</h3><p>Timestamped Finnish national consumption,
          production and load from authenticated sources, with retrieval provenance and stale-data indicators.</p>
          <div className="pill good">Operational context only</div>
          <Link href="/operations">Investigate observations ↗</Link></article>
      </div>
    </div></section>

    <section className="section"><div className="wrap">
      <div className="section-intro"><p className="eyebrow">Selection · source coverage</p>
        <h2>Five connection points in the current sample.</h2>
        <p>A deliberately small, auditable compilation. An unlisted point is not evidence of zero capacity.</p></div>
      <div className="grid-3">
        {nodes.map((n,i)=><Link key={n.connection_point_id} href={"/connections?point_id="+encodeURIComponent(n.connection_point_id)} className="point-card">
          <span className="kicker">0{i+1} · Fingrid</span>
          <h3>{n.name.replace(" 400 kV","")}</h3><p>{n.voltage_kv??"—"} kV transmission connection point</p>
          <span className="text-link">View recorded estimates ↗</span>
        </Link>)}
      </div>
      {nodes.length===0&&<p className="notice">No connection-point catalogue could be loaded from the evidence database.</p>}
    </div></section>

    <section className="section compact"><div className="wrap">
      <div className="feature-band"><div><p className="eyebrow">Methods · provenance</p><h2>No fabricated interpolation. No implied available megawatts.</h2></div>
        <div><p>Every numerical source estimate retains an original URL and capture timestamp.
          The 18 transcriptions are not independently operator-reconfirmed; missing
          year/direction combinations must remain unknown.</p>
        <div className="action-row"><Link className="button" href="/method">Read the evidence standard ↗</Link><Link className="button secondary" href="/api">REST API reference</Link></div></div>
      </div>
    </div></section>
  </>;
}
