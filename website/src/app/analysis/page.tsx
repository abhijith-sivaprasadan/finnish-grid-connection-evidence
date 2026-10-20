import type {Metadata} from "next";
import Link from "next/link";
import observed from "@/lib/finland-observed.json";
import scenario from "@/lib/pypsa-scenario-results.json";
import annualArchive from "@/lib/fingrid-archive-coverage-2025.json";
import winter from "@/lib/pypsa-long-winter-2025.json";
import {AnalysisWorkbench} from "@/components/analysis-workbench";

export const metadata:Metadata={title:"PyPSA Finland · historical system sensitivity"};
export default function Analysis(){
 return <section className="an-page">
  <header className="an-hero">
   <p className="an-kicker">PYPSA / FINLAND / SYSTEM-LEVEL RESEARCH</p>
   <h1>What changes when <em>100 MW</em> is added?</h1>
   <p>A source-grounded 48-hour national electricity-system sensitivity, solved with PyPSA and HiGHS. Actual Fingrid 2026 observations anchor the historical baseline; balancing limits, storage and flexible demand are clearly stated <strong>hypothetical assumptions</strong>.</p>
   <div className="an-hero-meta"><span>15–16 OCT 2026 UTC</span><span>192 × 15-MINUTE INTERVALS</span><span>ONE AGGREGATED BUS</span><span>4 SOLVED SCENARIOS</span></div>
  </header>
  <div className="cov-launch"><div><strong>Verified 2025 Fingrid source coverage</strong><p>{annualArchive.verified_complete_days} verified complete UTC days; {annualArchive.known_missing_source_days} known source-gap dates and {annualArchive.not_covered_by_archives_days} dates outside imported archives. Not physical connection capacity or a 365-day study.</p></div><Link href="/analysis/source-coverage">Inspect historical evidence ↗</Link></div>
  <div className="cov-launch"><div><strong>Source-verified 27-day winter modelling and Swedish-border market evidence</strong><p>{winter.scenario_count_all_caps} solved project cases across two uninterrupted 27-day winter periods, plus {winter.baseline_count} baselines; actual Fingrid 31/32 trade flows and unused 38/39 intraday market capacity. All constraints remain evidence-qualified, not grid rights.</p></div><Link href="/analysis/borders-2025">Inspect empirical border sensitivity ↗</Link></div>
  <div className="an-warning" role="note"><strong>Not a connection-capacity estimate.</strong> This model cannot determine whether a 100 MW project can connect at Seinäjoki, Uusnivala or any other named point. A modelled shortfall under an assumed balancing ceiling is <em>not</em> an observed Finnish blackout or actual transmission-grid limitation. These two days are not a 2030 forecast.</div>
  <AnalysisWorkbench observed={observed} model={scenario}/>
  <section className="an-reference">
   <div><p className="an-kicker">SOURCE DATA</p><h2>Auditable historical observations</h2>
    <p>Fingrid Open Data datasets 124 (consumption) and 74 (production), each reported as MWh/h averaged across its 15-minute interval. For energy calculations, the mean MW equivalent is multiplied by 0.25 h. The input preserves individual dataset retrieval timestamps; there is no synthetic historical generation or consumption.</p>
    <div className="an-link-row"><a href="https://data.fingrid.fi/en/datasets/124" target="_blank" rel="noreferrer">Consumption 124 ↗</a><a href="https://data.fingrid.fi/en/datasets/74" target="_blank" rel="noreferrer">Production 74 ↗</a></div></div>
   <div><p className="an-kicker">REPRODUCIBILITY</p><h2>Python, PyPSA and HiGHS</h2>
    <p>The observed aggregate generation is a fixed input; extra support, surplus disposal and shortfall are modelling constructs. The 1,500 MW external-support ceiling is a deliberately assumed stress test, not an observed import limit. All 4 cases solve to optimality and close the quarter-hour energy balance.</p>
    <div className="an-link-row"><a href="https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/blob/main/src/models/finland.py" target="_blank" rel="noreferrer">Model source ↗</a><Link href="/screening">Published connection evidence ↗</Link></div></div>
  </section>
 </section>;
}
