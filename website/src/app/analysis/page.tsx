import type {Metadata} from "next";
import Link from "next/link";
import observed from "@/lib/finland-observed.json";
import scenario from "@/lib/pypsa-scenario-results.json";
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
  <div className="dashboard-archive-link"><div><strong>New · 30-day PyPSA sensitivity study</strong><span>2,880 actual paired Fingrid intervals · 12 optimized combinations · hypothetical 1,000–2,000 MW balancing ceilings</span></div><Link href="/analysis/sensitivity">Compare verified results ↗</Link></div>
  <div className="dashboard-archive-link"><div><strong>Three-season PyPSA comparison · winter / summer / autumn 2025</strong><span>14 consecutive verified source days per season · missing intervals tracked · 36 optimizations, no annual or 2030 forecast</span></div><Link href="/analysis/seasons">Explore seasonal sensitivity ↗</Link></div>
  <div className="an-warning" role="note"><strong>Not a connection-capacity estimate.</strong> This model cannot determine whether a 100 MW project can connect at Seinäjoki, Uusnivala or any other named point. A modelled shortfall under an assumed balancing ceiling is <em>not</em> an observed Finnish blackout or actual transmission-grid limitation. These two days are not a 2030 forecast.</div>
  <AnalysisWorkbench observed={observed} model={scenario}/>
  <section className="an-reference">
   <div><p className="an-kicker">SOURCE DATA</p><h2>Auditable historical observations</h2>
    <p>Fingrid Open Data datasets 124 (consumption) and 74 (production), each reported as MWh/h averaged across its 15-minute interval. For energy calculations, the mean MW equivalent is multiplied by 0.25 h. The input preserves individual dataset retrieval timestamps; there is no synthetic historical generation or consumption.</p>
    <div className="an-link-row"><a href="https://data.fingrid.fi/en/datasets/124" target="_blank" rel="noreferrer">Consumption 124 ↗</a><a href="https://data.fingrid.fi/en/datasets/74" target="_blank" rel="noreferrer">Production 74 ↗</a></div></div>
   <div><p className="an-kicker">REPRODUCIBILITY</p><h2>Python, PyPSA and HiGHS</h2>
    <p>The observed aggregate generation is a fixed input; extra support, surplus disposal and shortfall are modelling constructs. The 1,500 MW external-support ceiling is a deliberately assumed stress test, not an observed import limit. All 4 cases solve to optimality and close the quarter-hour energy balance.</p>
    <div className="an-link-row"><a href="https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/blob/feature/pypsa-fi-demand-sensitivity/src/models/finland.py" target="_blank" rel="noreferrer">Model source ↗</a><Link href="/screening">Published connection evidence ↗</Link></div></div>
  </section>
 </section>;
}
