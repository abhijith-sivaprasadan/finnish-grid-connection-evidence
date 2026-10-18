import Link from "next/link";
import { NetworkVisual } from "@/components/network-visual";
import { overview, points } from "@/lib/repository";

export const dynamic = "force-dynamic";

export default async function Home() {
  const result = await Promise.allSettled([overview(), points(new URLSearchParams("limit=5"))]);
  const summary = result[0].status === "fulfilled" ? result[0].value : null;
  const nodes = result[1].status === "fulfilled" ? result[1].value.data : [];
  const latest = summary?.newest_operational_interval_utc;
  const age = latest ? Math.max(0, Math.floor((Date.now() - Date.parse(latest)) / 3600000)) : null;

  return <>
    <section className="hero">
      <div className="wrap hero-grid">
        <div className="hero-copy">
          <p className="eyebrow"><span className="eyebrow-dash" aria-hidden="true" /> FINLAND'S ELECTRICITY SYSTEM / INDEPENDENT RESEARCH</p>
          <h1>Grid evidence.<br /><span>Without the guesswork.</span></h1>
          <p className="lede">A clearer view of Finland's transmission connection outlook and national electricity data. Explore what has actually been published, where the gaps remain and what the numbers <strong>cannot</strong> tell you.</p>
          <div className="action-row">
            <Link href="/connections" className="button">Explore connection evidence <span aria-hidden="true">↗</span></Link>
            <Link href="/method" className="button secondary">How the evidence works <span aria-hidden="true">→</span></Link>
          </div>
          <div className="hero-trust" aria-label="Platform characteristics">
            <span><span className="check-symbol" aria-hidden="true">✓</span> Original source links</span>
            <span><span className="check-symbol" aria-hidden="true">✓</span> Clearly stated limits</span>
            <span><span className="check-symbol" aria-hidden="true">✓</span> Public REST API</span>
          </div>
        </div>
        <NetworkVisual />
      </div>
    </section>

    <section className="metrics-section">
      <div className="wrap">
        {!summary && <p className="notice warn" role="status">The evidence store could not be read. No invented counts are shown.</p>}
        {summary?.data_mode === "compiled_snapshot" && <div className="data-status" role="status">
          <span className="data-status-icon" aria-hidden="true">i</span>
          <div><strong>Public snapshot mode</strong><span>Connection figures are the source-transcribed 17 October 2026 compilation, not live Fingrid results. Independent numeric recheck is pending. Operational data need the database connection.</span></div>
          <Link href="/method">About this dataset ↗</Link>
        </div>}
        <div className="metrics-heading"><span className="eyebrow">AT A GLANCE</span><span className="metrics-caption">Coverage of the current research sample · not the full Finnish grid</span></div>
        <div className="data-strip" aria-label="Available evidence counts">
          <div><span className="metric-icon" aria-hidden="true">01</span><strong>{summary?.points ?? "—"}</strong><span>Named 400 kV connection points</span></div>
          <div><span className="metric-icon" aria-hidden="true">02</span><strong>{summary?.capacity_observations ?? "—"}</strong><span>Indicative source observations</span></div>
          <div><span className="metric-icon" aria-hidden="true">03</span><strong>{summary?.data_mode === "compiled_snapshot" ? "—" : summary?.operational_rows_stored ?? "—"}</strong><span>Stored national operational records</span></div>
          <div><span className="metric-icon" aria-hidden="true">04</span><strong>{age === null ? "—" : age + "h"}</strong><span>Age of latest national interval · UTC</span></div>
        </div>
        {age !== null && age > 120 && <p className="notice warn" role="status">Newest operational record is over five days old. National measurements should not be described as live.</p>}
      </div>
    </section>

    <section className="section research-section"><div className="wrap">
      <div className="section-topline"><p className="eyebrow">EXPLORE THE EVIDENCE</p><span className="section-index">01 / 03</span></div>
      <div className="section-intro split-heading">
        <h2>One grid.<br /><span>Different kinds of evidence.</span></h2>
        <p>Connection estimates and national system measurements answer different questions. We keep them separate—so the interpretation stays useful.</p>
      </div>
      <div className="grid-2">
        <article className="research-card track-card">
          <div className="track-icon" aria-hidden="true"><span className="line-icon line-icon-nodes" /></div>
          <span className="kicker">CONNECTION OUTLOOK · GRID SCOPE</span>
          <h3>Where might new connections be possible?</h3>
          <p>Browse published, conditional estimates by 400 kV point, production or consumption direction and effective year. Every reported value links to its source.</p>
          <div className="track-bottom"><span className="pill note">Independent recheck pending</span><Link href="/connections" className="text-link">Explore points <span aria-hidden="true">↗</span></Link></div>
        </article>
        <article className="research-card track-card track-card-soft">
          <div className="track-icon" aria-hidden="true"><span className="line-icon line-icon-chart" /></div>
          <span className="kicker">SYSTEM DATA · FINGRID + ENTSO-E</span>
          <h3>How does the national grid operate over time?</h3>
          <p>Examine timestamped consumption, production and actual-load records, where the connected source store is available. These are not measurements of local connection headroom.</p>
          <div className="track-bottom"><span className="pill good">National context only</span><Link href="/operations" className="text-link">View system data <span aria-hidden="true">↗</span></Link></div>
        </article>
      </div>
    </div></section>

    <section className="section directory-section"><div className="wrap">
      <div className="section-topline"><p className="eyebrow">THE POINT INDEX</p><span className="section-index">02 / 03</span></div>
      <div className="section-intro split-heading">
        <h2>A focused sample.<br /><span>Every source accounted for.</span></h2>
        <p>Five named transmission points currently form the published sample. This is an auditable starting point—not an inventory of all substations or their remaining capacity.</p>
      </div>
      <div className="point-directory">
        {nodes.map((n, i) => <Link key={n.connection_point_id}
          href={"/connections?point_id=" + encodeURIComponent(n.connection_point_id)}
          className="directory-row">
          <span className="directory-number">{String(i + 1).padStart(2, "0")}</span>
          <span className="directory-name">{n.name.replace(" 400 kV", "")}<small>Fingrid · published source sample</small></span>
          <span className="directory-voltage">{n.voltage_kv ?? "—"} kV</span>
          <span className="directory-arrow" aria-hidden="true">↗</span>
        </Link>)}
      </div>
      {nodes.length === 0 && <p className="notice">The connection-point catalogue is currently unavailable. No replacement sample is shown.</p>}
      <p className="directory-foot">Unlisted points and absent year/direction values must not be interpreted as zero capacity. <Link href="/method">Read the limitations →</Link></p>
    </div></section>

    <section className="section conclusion-section"><div className="wrap">
      <div className="section-topline"><p className="eyebrow">RESEARCH BY DESIGN</p><span className="section-index">03 / 03</span></div>
      <div className="conclusion-band">
        <div><span className="conclusion-kicker">TRANSPARENT BY DEFAULT</span>
          <h2>A useful atlas knows<br />the limits of its map.</h2></div>
        <div className="conclusion-side">
          <p>Numbers are conditional. Sources have capture dates. Missing entries are unknown. We never add substation estimates together or pass national load figures off as available megawatts.</p>
          <div className="action-row"><Link href="/method" className="button light">Understand the methodology ↗</Link><Link href="/api" className="button ghost">Explore the API →</Link></div>
        </div>
      </div>
    </div></section>
  </>;
}
