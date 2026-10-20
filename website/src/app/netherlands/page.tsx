import type {Metadata} from "next";
import Link from "next/link";
import audit from "@/lib/netherlands-official-source-summary-2026.json";

export const metadata:Metadata={
 title:"Netherlands grid congestion · official source audit",
 description:"Evidence-qualified Dutch TenneT and regional network capacity-map CSV intake, reproducible original hashes, consumption and feed-in codes, without unverified connection capacity."
};

const total=audit.original_csvs.reduce((sum,item)=>sum+item.row_count,0);
const congest=audit.original_csvs.find(s=>s.key==="tennet_congestion");
if(!congest||!("original_label_counts" in congest))throw new Error("Original TenneT categories missing");
const consumption=congest.original_label_counts.afname;
const injection=congest.original_label_counts.opwek;

export default function NetherlandsPilot(){
 return <>
 <section className="page-hero"><div className="wrap">
  <p className="eyebrow">Europe / Netherlands / verified CSV source intake</p>
  <h1>Congestion data, <em>without fabricated capacity.</em></h1>
  <p className="lede">A second-market data engineering pilot using three original Netbeheer Nederland national capacity-map exports. The recorded inputs cover high-voltage feeding areas, TenneT congestion categories and regional DSO feeding areas. This is an <strong>as-captured source audit</strong>, not a live site feasibility tool.</p>
  <div className="action-row">
   <a className="button" href={audit.source_homepage} target="_blank" rel="noreferrer">Original Netherlands capacity map ↗</a>
   <Link className="button secondary" href="/screening">Finland connection-pathway screen ↗</Link>
  </div>
 </div></section>
 <section className="section compact"><div className="wrap">
  <div className="data-strip three">
   <div><strong>{audit.original_csvs.length}</strong><span>Official CSV export schemas verified</span></div>
   <div><strong>{total}</strong><span>Original source records checked, not individual available sites</span></div>
   <div><strong>{audit.captured_date_utc}</strong><span>UTC date of saved source snapshot</span></div>
  </div>
  <p className="footnote">The exporter retains only file hashes, schemas, aggregated counts and explicit rights notes. Raw Dutch rows and location identifiers are not published; their derivative redistribution licence has not been verified.</p>
 </div></section>
 <section className="section"><div className="wrap">
  <div className="section-intro"><p className="eyebrow">Original transmission and distribution evidence</p><h2>Three layers, not one interchangeable capacity number.</h2><p>The Netherlands capacity map distinguishes operator level, source direction and future expansions. Different rows are not deduplicated individual grid connection opportunities.</p></div>
  <div className="grid-2">{audit.original_csvs.map(source=><article className="research-card" key={source.key}>
   <span className="kicker">{source.key.replaceAll("_"," ").toUpperCase()}</span>
   <h3>{source.name}</h3><p><strong>{source.row_count} records</strong> · {source.field_count} original CSV columns · SHA-256 verified</p>
   <p style={{overflowWrap:"anywhere",fontSize:12}}><code>{source.sha256}</code></p>
   <a href={source.url} target="_blank" rel="noreferrer">Open official source export ↗</a>
  </article>)}</div>
 </div></section>
 <section className="section compact"><div className="wrap">
  <div className="section-intro"><p className="eyebrow">TenneT source-only aggregation</p><h2>Consumption and injection are different data.</h2><p>These counts reproduce the original untranslated code labels. Their interpretation as available / constrained / unavailable capacity is deliberately <strong>not inferred</strong> from a code alone.</p></div>
  <div className="table-wrap"><table><thead><tr><th>Original code</th><th>Consumption · afname</th><th>Feed-in · opwek</th><th>Interpretation</th></tr></thead>
   <tbody>{(["0","1","3"] as const).map(code=><tr key={code}><td>{code}</td><td>{consumption[code]}</td><td>{injection[code]}</td><td>Unmapped original categorical indicator</td></tr>)}</tbody>
  </table></div>
  <p className="source-note">The feeding-area congestion records are not uniquely identified customer applications. The original map's waiting-list MW measure is requested but unallocated demand; neither it nor total installed transport capacity is spare grid MW available to new data centres.</p>
 </div></section>
 <section className="section"><div className="wrap">
  <div className="feature-band">
   <div><p className="eyebrow">What we can and cannot decide</p><h2>One pipeline, two countries, two evidence definitions.</h2></div>
   <div><p><strong>Finland:</strong> selected exact-year, source-reviewed Fingrid Grid Scope MW estimates plus a separate voltage/connection-pathway check.</p>
   <p><strong>Netherlands:</strong> real network-operator-fed congestion and waiting-list source schemas/metadata from a national capacity map, without site-specific MW or transport-rights claims.</p>
   <p>No numerical comparison of a Dutch congestion code with a Finnish substation MW threshold is justified.</p></div>
  </div>
  <div className="limit-box"><span className="kicker">Data and scientific boundary</span>
  <p>Official map content is an indicative snapshot, not binding TenneT/DSO connection permission. The three sources capture data levels that differ in meaning; colour/code interpretation and dataset redistribution rights require separate verification. Original records remain on the source publisher's website. Re-run the original downloader to audit new revisions; never call the dated counts live.</p></div>
  <div className="source-links">
   <a href={audit.source_homepage} target="_blank" rel="noreferrer">Netbeheer Nederland capacity-map information <span>Operator map definitions ↗</span></a>
   <a href={audit.source_faq} target="_blank" rel="noreferrer">Official FAQ <span>Congestion / queue / planned-expansion terminology ↗</span></a>
   <a href={audit.original_audit_run} target="_blank" rel="noreferrer">Source verification run <span>Reproducible originals and unit tests ↗</span></a>
   <Link href="/api/v1/netherlands/source-summary">Read-only machine-readable metadata →</Link>
  </div>
 </div></section>
 </>;
}
