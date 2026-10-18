import type { Metadata } from "next";
import Link from "next/link";
import { overview, capacities } from "@/lib/repository";
import { qualityReport, auditRecords, FEEDS } from "@/lib/workbench";
import { QualityWorkbench } from "@/components/quality-workbench";
export const dynamic="force-dynamic";
export const metadata:Metadata={title:"Data quality and source audit"};
export default async function QualityPage(){
  let fault:string|null=null;
  let summary:Awaited<ReturnType<typeof overview>>|null=null;
  let quality:Awaited<ReturnType<typeof qualityReport>>|null=null;
  let audits:ReturnType<typeof auditRecords>=[];
  try {
    summary=await overview();
    const records=await capacities(new URLSearchParams("limit=200"));
    audits=auditRecords(records.data);
    if(summary.data_mode==="neon"&&summary.newest_operational_interval_utc)
      quality=await qualityReport(summary.newest_operational_interval_utc);
  } catch {fault="The source evidence database is temporarily unavailable. Quality statistics are not fabricated.";}
  return <>
    <section className="page-hero"><div className="wrap"><p className="eyebrow">03 / Provenance and integrity</p>
      <h1>Trust the <em>evidence trail.</em></h1>
      <p className="lede">See exactly what was recorded, how complete each day is, where retrieval revisions exist, and what still needs an independent operator check.</p></div></section>
    <section className="section compact"><div className="wrap">
      {fault&&<p role="alert" className="notice warn">{fault}</p>}
      {quality&&summary&&<>
        <div className="data-strip three">
          <div><strong>{quality.distinctIntervals}</strong><span>Distinct source intervals · 30-day observed window</span></div>
          <div><strong>{quality.retrievalRevisions}</strong><span>Additional retrieval versions · not additional intervals</span></div>
          <div><strong>{summary.operational_rows_stored}</strong><span>All-time stored rows · includes retrieval revisions</span></div>
        </div>
        <QualityWorkbench rows={quality.rows} to={quality.to}/>
        <div className="section-intro table-heading"><p className="eyebrow">SOURCE COVERAGE</p><h2>Evidence by feed.</h2></div>
        <div className="table-wrap"><table><thead><tr><th>Source</th><th>Recorded UTC days</th><th>Complete UTC days</th><th>Distinct intervals</th><th>Stored revisions</th></tr></thead><tbody>
          {quality.sources.map(s=><tr key={s.dataset_id}><th>{s.label} ({s.dataset_id})</th>
            <td>{s.recordedDays}</td><td>{s.completeDays}</td><td>{s.uniqueIntervals}</td><td>{s.retrievalRevisions}</td></tr>)}
        </tbody></table></div>
        <p className="chart-caption">The completeness heatmap anchors its 30-day window on the newest stored interval. An unrecorded day is not evidence of a source outage. Historical retrieval revisions remain counted separately. View <Link href="/api/v1/quality">quality JSON ↗</Link>.</p>
      </>}
      {!quality&&!fault&&<p className="notice">No Neon operational intervals available to calculate quality. The capacity audit remains available below.</p>}
      <section id="audit" className="audit-section" aria-label="Independent Grid Scope evidence audit">
        <div className="wb-heading"><div><p className="eyebrow">FINGRID GRID SCOPE / NUMERIC RECHECK</p>
          <h2>18 source observations. No independent certificates.</h2>
          <p>The original 17 October 2026 transcription is preserved. The public operator describes its connection estimates as rough and non-guaranteed. The interactive map has not yielded a reproducible independent number-by-number audit.</p></div>
          <a className="button secondary" href="/api/v1/export/recheck">Download 18-row reviewer worksheet ↓</a>
        </div>
        <div className="quality-strip"><div><strong>{audits.length}</strong><span>Source-transcribed observations</span></div>
          <div><strong>0</strong><span>Independently rechecked here</span></div>
          <div><strong>{audits.length}</strong><span>Pending numerical audit</span></div></div>
        <div className="table-wrap"><table><thead><tr><th>Substation</th><th>Direction</th><th>Effective year</th><th>Transcribed</th><th>Review state</th><th>Original evidence</th></tr></thead>
          <tbody>{audits.map(a=><tr key={a.observation_id}>
            <td>{a.name}</td><td>{a.direction}</td><td>{a.effective_year}</td><td>{a.capacity_value} {a.capacity_unit}</td>
            <td><span className="pill note">Pending recheck</span></td>
            <td><a href={a.source_url} target="_blank" rel="noreferrer">Fingrid viewer ↗</a></td></tr>)}</tbody>
        </table></div>
        <p className="chart-caption">A reviewer must check point identity, voltage, selected generation/consumption layer, effective year, MW/MVA unit and exact numeric value, then retain dated evidence. Changed current publications must be stored as new captures—not destructive edits. <a href="https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/" rel="noreferrer" target="_blank">Official source limitations ↗</a></p>
      </section>
    </div></section>
  </>;
}
