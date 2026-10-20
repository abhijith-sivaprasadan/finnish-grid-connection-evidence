import type {Metadata} from "next";
import Link from "next/link";
import winter from "@/lib/pypsa-long-winter-2025.json";
import borders from "@/lib/pypsa-border-observed-2025.json";
export const metadata:Metadata={title:"Observed Swedish-border markets and winter PyPSA | Finland"};
const fmt=(n:number)=>n.toLocaleString("en-US",{maximumFractionDigits:1});
export default function HistoricalBorderResearch(){
return <section className="vse-page">
<header className="vse-hero">
<p className="vse-kicker">ACTUAL FINGRID HISTORY / SEPARATE HYPOTHETICAL MODELS</p>
<h1>From arbitrary bounds to <em>observed market evidence.</em></h1>
<p>Two independently continuous 27-day winter system model windows, plus a distinct project-only PyPSA scenario constrained by historical published Sweden→Finland unused intraday commercial import capacity.</p>
<div className="vse-hero-metrics"><span>2 × 27 source-verified winter days</span><span>48 actual winter project solves</span><span>30 days measured market context</span></div>
</header>
<div className="vse-caveat"><strong>Not a 2030 grid-connection study.</strong> The earlier national model still uses assumed 1,000–2,000 MW balancing stress caps. The border model uses Fingrid 38 and 39 observed unused intraday trading capacity AFTER day-ahead allocation. This is neither physical transmission headroom nor import rights. No national outages are inferred.</div>
<section className="vse-panel"><p className="vse-kicker">01 / REAL WINTER SOURCE WINDOWS</p><h2>Demand flexibility, 100 MW batteries and duration</h2>
<p className="vse-note">The values below are verified optimized incremental **fictional stress slack**, relative to each window's no-project reference under the SAME ASSUMED 1,500 MW national balancing bound. Each 27-day period preserves 2,592 authentic contiguous 15-minute source pairs; load energy is exactly 64,800 MWh per case.</p>
{winter.model_windows.map(w=><div key={w.id}><h3>{w.id==="winter27"?"Winter: Jan 18–Feb 13":"Late winter: Feb 15–Mar 13"} 2025</h3>
<p className="vse-note">Original CSV SHA-256: <code>{w.source_sha256}</code></p>
<div className="vse-table-overflow"><table className="vse-table"><thead><tr><th>Assumed flex</th><th>100 MW battery</th><th>Incremental penalty slack</th></tr></thead>
<tbody>{w.scenarios.map((x,i)=><tr key={i}><td>{x.flex_half_span_mw===0?"Flat 100 MW":"Energy-neutral ±50 MW"}</td><td>{x.battery_duration_hours===0?"None":String(x.battery_duration_hours)+" hours"}</td><td>{fmt(x.incremental_model_penalty_slack_mwh)} MWh</td></tr>)}</tbody></table></div></div>)}
<p className="vse-note">Both 27-day optimizations and their battery states are independent, not one continuous 54-day operation. February 14 had original missing observations. The full three assumed national cap grid and 6 reference solutions remain in the original solver artifact.</p>
<a href={"https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/"+winter.source_run} target="_blank" rel="noreferrer">Verified 27-day original sources and 54 total HiGHS solves ↗</a>
</section>
<section className="vse-panel"><p className="vse-kicker">02 / ORIGINAL SWEDISH BORDER MARKET OBSERVATIONS</p><h2>Actual historical market flows and remaining trading capacity</h2>
<div className="vse-overview">
<div><small>FI→SE1 SIGNED COMMERCIAL</small><strong>{fmt(borders.observed_statistics.fi_se1_commercial_signed_mean_mw)} MW</strong><span>Negative = FI commercial import</span></div>
<div><small>FI→SE3 SIGNED COMMERCIAL</small><strong>{fmt(borders.observed_statistics.fi_se3_commercial_signed_mean_mw)} MW</strong><span>Negative = FI commercial import</span></div>
<div><small>SE1+SE3→FI UNUSED INTRADAY</small><strong>{fmt(borders.observed_statistics.unused_intraday_import_SE1_SE3_median_mw)} MW</strong><span>Median remaining market capacity, not physical grid headroom</span></div>
<div><small>15-MIN INTERVALS AT ≥100 MW</small><strong>{(borders.observed_statistics.quarter_hour_share_unused_intraday_capacity_at_least_100mw*100).toFixed(1)}%</strong><span>Market observation, not capacity entitlement</span></div>
</div>
<div className="vse-table-overflow"><table className="vse-table"><thead><tr><th>Original dataset</th><th>Source meaning</th><th>SHA-256 pinned</th></tr></thead><tbody>{[
{n:"31",role:"FI-SE1 commercial, positive FI export"},
{n:"32",role:"FI-SE3 commercial, positive FI export"},
{n:"38",role:"Unused SE1→FI intraday import after day-ahead"},
{n:"39",role:"Unused SE3→FI intraday import after day-ahead"}].map(item=><tr key={item.n}>
<th><a href={"https://data.fingrid.fi/en/datasets/"+item.n} target="_blank" rel="noreferrer">{item.n} ↗</a></th><td>{item.role}</td><td><code>{borders.source_sha256_by_dataset[item.n as keyof typeof borders.source_sha256_by_dataset].slice(0,16)}…</code></td></tr>)}</tbody></table></div>
<p className="vse-note">All 2,880 original quarter-hour observations were verified for each of the four operator datasets during September 15–October 14, 2025. Original signed commercial flows and published unused intraday capacity are different physical and market concepts.</p></section>
<section className="vse-panel"><p className="vse-kicker">03 / CONDITIONAL MARGINAL MARKET ACCESS</p><h2>What if a 100 MW new project could participate in unused intraday trading space?</h2>
<p className="vse-note">A completely separate project-only PyPSA model applies the genuine time-varying SE1+SE3 unused intraday market capacity as an empirical <strong>conditional trading-space ceiling</strong>. It does not model Finnish national supply, domestic congestion, generator deliverability, or project import rights.</p>
<div className="vse-table-overflow"><table className="vse-table"><thead><tr><th>Assumed load flexibility</th><th>100 MW battery duration</th><th>Hypothetical project-unmet relaxation</th></tr></thead>
<tbody>{borders.scenarios.map((x,i)=><tr key={i}><td>{x.flex_half_span_mw===0?"Flat 100 MW":"Energy-neutral ±50 MW"}</td><td>{x.battery_duration_hours===0?"None":String(x.battery_duration_hours)+" hours"}</td><td>{fmt(x.modelled_project_penalty_relaxation_mwh)} MWh</td></tr>)}</tbody></table></div>
<p className="vse-note">Model relaxation is not observed unmet load or actual avoided outages, nor does it mean an operator will sell or deliver this market capacity. The result cannot be compared as the same stress metric to the national arbitrary-cap model.</p>
<a href={"https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/"+borders.source_run} target="_blank" rel="noreferrer">Original border CSV readings + eight verified conditional solves ↗</a>
</section>
<section className="vse-panel vse-limitations"><p className="vse-kicker">04 / EVIDENCE BOUNDARIES</p><h2>Do not confuse market trading space with grid rights</h2>
{borders.limitations.map((x,i)=><p key={i}>{x}</p>)}
<p><Link href="/analysis/corridors-2025">Inspect the new separate SE1/SE3 source-capped market corridor model ↗</Link></p><Link href="/analysis/source-coverage">Original 2025 observation coverage ↗</Link>
</section>
</section>;
}
