import type {Metadata} from "next";
import Link from "next/link";
import data from "@/lib/pypsa-extended-sensitivity.json";
import {ExtendedSensitivity} from "@/components/extended-sensitivity";
export const metadata:Metadata={title:"30-day PyPSA sensitivity · Finland historical research"};
export default function ExtendedStudy(){
 return <section className="lh-page">
  <header className="lh-hero">
   <p className="lh-kicker">FINLAND / PYPSA / EXTENDED HISTORICAL RESEARCH</p>
   <h1>30 days. <em>12 scenario sensitivities.</em></h1>
   <p>We paired real national Fingrid electricity consumption and production observations from 15 September to 14 October 2025, then varied assumed balancing limits, load flexibility and battery power in an independently verified PyPSA model.</p>
   <div className="lh-hero-facts"><span>2,880 source pairs</span><span>15-minute intervals</span><span>12 optimizations</span><span>3 reference solves</span></div>
  </header>
  <div className="lh-limit" role="note"><strong>Not real shortages or connection headroom.</strong> All displayed deficit values are modelled penalty slack under <em>invented</em> 1,000–2,000 MW balancing ceilings. The results do not represent Finnish blackouts, actual cross-border capacity, availability at any substation, or a 2030 forecast.</div>
  <ExtendedSensitivity data={data}/>
  <section className="lh-evidence">
   <div><p className="lh-kicker">ORIGINAL OPERATOR OBSERVATIONS</p>
    <h2>Complete, source-linked historical period</h2>
    <p>Fingrid datasets 124 (consumption) and 74 (production) supply 2,880 paired 15-minute intervals in MWh/h. The authenticated retrieval is validated for missing, duplicate and mismatched observations, then archived as a CSV with original timestamps and a SHA-256 manifest.</p>
    <div className="lh-source-links"><a target="_blank" rel="noreferrer" href="https://data.fingrid.fi/en/datasets/124">Fingrid 124 ↗</a><a target="_blank" rel="noreferrer" href="https://data.fingrid.fi/en/datasets/74">Fingrid 74 ↗</a><a target="_blank" rel="noreferrer" href={data.source_run.workflow_url}>Download validated run artifact ↗</a></div>
   </div>
   <div><p className="lh-kicker">MODEL PROVENANCE</p>
    <h2>Rerunnable PyPSA/HiGHS study</h2>
    <p>All parameter combinations returned optimal, balanced solutions. Additional demand is fixed at 100 MW on average (72,000 MWh across 30 days). Flexibility redistributes that energy each UTC day using observed residual demand as hindsight. The assumed battery has 4 hours of energy and 90% round-trip efficiency.</p>
    <p className="lh-hash">Original input SHA-256: <code>{data.source_csv_sha256}</code></p>
    <div className="lh-source-links"><Link href="/analysis">Original 48-hour study ↗</Link><Link href="/screening">Separate site evidence ↗</Link></div>
   </div>
  </section>
 </section>;
}
