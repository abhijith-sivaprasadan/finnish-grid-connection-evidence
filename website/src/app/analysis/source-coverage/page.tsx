import type {Metadata} from "next";
import Link from "next/link";
import evidence from "@/lib/fingrid-archive-coverage-2025.json";

export const metadata:Metadata={title:"2025 Fingrid historical source coverage · Finland"};

const months=["January","February","March","April","May","June","July","August","September","October","November","December"];
type DayStatus="complete"|"source_missing"|"not_in_archives";
const windows=evidence.original_source_windows.map(w=>({start:Date.parse(w.start+"T00:00:00Z"),end:Date.parse(w.end_exclusive+"T00:00:00Z")}));
const missing=new Set(evidence.known_missing_original_124_intervals_utc.map(s=>s.slice(0,10)));
const days=Array.from({length:365},(_,i)=>{
 const d=new Date(Date.UTC(2025,0,1+i));
 const label=d.toISOString().slice(0,10);
 const status:DayStatus=windows.some(w=>d.getTime()>=w.start&&d.getTime()<w.end)
  ?"complete":missing.has(label)?"source_missing":"not_in_archives";
 return {date:label,day:d.getUTCDate(),month:d.getUTCMonth(),status};
});
const labels:Record<DayStatus,string>={
 complete:"Source-complete paired observations",
 source_missing:"Known source-missing consumption observation",
 not_in_archives:"Not covered by imported archives; unknown outside these captures"
};
const counts={
 complete:days.filter(d=>d.status==="complete").length,
 source_missing:days.filter(d=>d.status==="source_missing").length,
 not_in_archives:days.filter(d=>d.status==="not_in_archives").length
};
if(counts.complete!==evidence.verified_complete_days||
 counts.source_missing!==evidence.known_missing_source_days||
 counts.not_in_archives!==evidence.not_covered_by_archives_days)
 throw new Error("Pinned original source report differs from 2025 UTC calendar");

export default function ArchiveCoverage(){
 return <section className="cov-page">
  <header className="cov-hero">
    <p className="cov-kicker">FINGRID / REAL ORIGINAL SOURCE AUDIT / 2025</p>
    <h1>What history do we <em>actually have?</em></h1>
    <p>A fingerprint-verified inventory of paired national consumption and production observations, assembled entirely from existing GitHub Actions archives. No new operator API calls; unknown dates remain unknown.</p>
    <div className="cov-meta"><span>Original source datasets 124 + 74</span><span>2025 UTC calendar</span><span>Not a full-year data series</span></div>
  </header>
  <div className="cov-warning"><strong>This is source coverage, not grid capability.</strong> The map below describes which original historical observations have been imported and verified. It does not describe national power shortages, 2030 demand forecasts, balancing headroom or the feasibility of any 100 MW grid connection.</div>
  <div className="cov-stats">
   <div><small>PAIRED HISTORICAL DAYS</small><strong>{evidence.verified_complete_days}</strong><span>Only the verified original-source windows</span></div>
   <div><small>PAIRED 15-MINUTE READINGS</small><strong>{evidence.distinct_original_paired_intervals.toLocaleString("en-US")}</strong><span>Verified Fingrid 124 and 74 observations</span></div>
   <div><small>KNOWN OPERATOR-SOURCE GAP DAYS</small><strong>{counts.source_missing}</strong><span>Three missing readings across two UTC dates</span></div>
   <div><small>NOT COVERED BY THESE ARCHIVES</small><strong>{counts.not_in_archives}</strong><span>May be available from Fingrid; not yet audited here</span></div>
  </div>
  <section className="cov-panel">
   <p className="cov-kicker">01 / SOURCE COVERAGE BY UTC CALENDAR DAY</p>
   <h2>365 days, three distinct evidence states</h2>
   <div className="cov-legend"><span><i className="cov-complete"/>Verified original source pairs</span><span><i className="cov-source_missing"/>Source gap confirmed on recheck</span><span><i className="cov-not_in_archives"/>Not covered by imported archives</span></div>
   <div className="cov-months" aria-label="Daily Fingrid source coverage during 2025">
    {months.map((month,index)=><div className="cov-month" key={month}>
      <div className="cov-month-name"><strong>{month}</strong><small>{days.filter(d=>d.month===index&&d.status==="complete").length} verified</small></div>
      <div className="cov-month-days">{days.filter(d=>d.month===index).map(d=><span key={d.date} className={"cov-date cov-"+d.status} title={d.date+" — "+labels[d.status]} aria-label={d.date+" — "+labels[d.status]}>{d.day}</span>)}</div>
     </div>)}
   </div>
   <p className="cov-caption">An uncovered date does not mean Fingrid has no data; it means that date has not been verified in this particular archive bank. Jan 17 and Jul 11 are independently documented original-source gap dates.</p>
  </section>
  <section className="cov-panel">
   <p className="cov-kicker">02 / CONTIGUOUS, SOURCE-COMPLETE PERIODS</p><h2>Original-data windows ready for separate historical modelling</h2>
   <div className="cov-table-scroll"><table className="cov-table"><thead><tr><th>Original capture</th><th>UTC start</th><th>UTC end (exclusive)</th><th>Days</th></tr></thead>
    <tbody>{evidence.original_source_windows.map(w=><tr key={w.label}><th>{w.label}</th><td>{w.start}</td><td>{w.end_exclusive}</td><td>{w.days}</td></tr>)}</tbody>
   </table></div>
   <p className="cov-caption">These windows may be modelled separately under documented PyPSA assumptions; they cannot be concatenated into an uninterrupted year-long storage operation. The autumn 14-day overlap was checked against the 30-day capture, not double-counted.</p>
  </section>
  <section className="cov-provenance">
   <div><p className="cov-kicker">OPERATOR DATA AND CODE VERIFICATION</p><h2>Independently reproducible inputs</h2><p>Original source fingerprints, native MWh/h units, 15-minute interval continuity and overlapping autumn numerical observations were validated without querying Fingrid again. See the CI result for the full audit.</p>
    <div className="cov-links"><a href={evidence.validation_run} target="_blank" rel="noreferrer">Verified archive job ↗</a><a href="https://data.fingrid.fi/en/datasets/124" target="_blank" rel="noreferrer">Fingrid 124 ↗</a><a href="https://data.fingrid.fi/en/datasets/74" target="_blank" rel="noreferrer">Fingrid 74 ↗</a></div></div>
   <div><p className="cov-kicker">KNOWN SOURCE GAPS</p><h2>Do not fill missing observations</h2><p>Six original consumption quarter-hours are known missing across four source-gap dates; the earlier three were independently rechecked and still not returned. The problem is tracked as an original-data correction request, not a grid-connection infeasibility determination.</p><div className="cov-links"><a href={evidence.missing_recheck_run} target="_blank" rel="noreferrer">Missing-readings recheck ↗</a><a href="https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/issues/40" target="_blank" rel="noreferrer">Operator correction issue ↗</a><Link href="/analysis/seasons">Validated seasonal PyPSA results ↗</Link></div></div>
  </section>
 </section>;
}
