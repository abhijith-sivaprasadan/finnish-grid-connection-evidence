import type {Metadata} from "next";
import Link from "next/link";
import study from "@/lib/pypsa-verified-seasonal-2025.json";
import {VerifiedSeasonalComparison} from "@/components/verified-seasonal-comparison";

export const metadata:Metadata={title:"Verified 2025 seasonal PyPSA comparison | Finland"};
export default function SeasonalStudy(){
 return <section className="vse-page">
   <header className="vse-hero">
    <p className="vse-kicker">FINLAND / FINGRID HISTORICAL EVIDENCE / PYPSA</p>
    <h1>Three seasons. <em>Verified source windows.</em></h1>
    <p>Compare a hypothetical additional 100 MW of electricity consumption across three equal-length 2025 historical windows. Original Fingrid readings remain separate from PyPSA's invented balancing and flexibility assumptions.</p>
    <div className="vse-hero-metrics"><span>14 consecutive days / season</span><span>1,344 paired intervals / season</span><span>36 verified scenario solves</span></div>
   </header>
   <div className="vse-caveat" role="note">
    <strong>Observed source data does not imply grid feasibility.</strong> These are three selected, consecutive 14-day samples—not full seasons or a validated calendar-year study. Modelled penalty slack under arbitrary balancing limits is neither measured Finnish outages nor confirmed import or substation headroom. No 2030 forecast is made.
   </div>
   <div className="dashboard-archive-link"><div><strong>Original Fingrid 2025 archive coverage</strong><span>125 historical source-complete days from independently validated artifacts · full-year input unavailable</span></div><Link href="/analysis/source-coverage">Inspect original-source coverage ↗</Link></div>
   <VerifiedSeasonalComparison study={study}/>
   <section className="vse-source">
    <div><p className="vse-kicker">SOURCE VALIDATION</p><h2>Missing values remain missing</h2>
     <p>The full-year source-completeness audit was rejected. Fingrid 124's sampled winter 30-day window was missing two quarter-hour readings, and summer was missing one. Those dates are recorded in source-audit metadata; no gap was interpolated, copied from another year or treated as zero. Autumn's original 30 days passed.</p>
     <p>Each modelled interval is present in both original Fingrid source datasets and preserved with a reproducible source checksum and capture timestamp.</p>
     <div className="vse-links"><a href="https://data.fingrid.fi/en/datasets/124" target="_blank" rel="noreferrer">Consumption dataset 124 ↗</a><a href="https://data.fingrid.fi/en/datasets/74" target="_blank" rel="noreferrer">Production dataset 74 ↗</a></div>
    </div>
    <div><p className="vse-kicker">REPRODUCIBILITY</p><h2>Real PyPSA/HiGHS optimization</h2>
     <p>Each selected period has twelve optimal, energy-balanced model scenarios, with matching no-project reference cases at each assumed balancing ceiling. Source CSV files, model reports and the missing-interval audit are retained in the authenticated GitHub Actions artifact.</p>
     <div className="vse-links"><a href={study.source_validation_run} target="_blank" rel="noreferrer">Verified workflow and artifacts ↗</a><Link href="/analysis/sensitivity">30-day autumn study ↗</Link><Link href="/analysis">48-hour original study ↗</Link></div>
    </div>
   </section>
 </section>;
}
