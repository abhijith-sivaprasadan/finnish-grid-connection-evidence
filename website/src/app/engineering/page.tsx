import type {Metadata} from "next";
import Link from "next/link";
import {EngineeringScenarioExplorer} from "@/components/engineering-scenario-explorer";
import report from "@/lib/krios-engineering-verified-2026.json";
export const metadata:Metadata={title:"Electrical engineering lab · CIGRE and PyPSA",description:"Verified pandapower HV/MV AC, N−1, independent PyPSA nonlinear AC comparison and hypothetical Finnish regional sensitivity."};
export default function Engineering(){
 return <><section className="page-hero"><div className="wrap">
 <p className="eyebrow">BENCHMARK ENGINEERING / VERIFIED SOLVER OUTPUT</p>
 <h1>Test electrical <em>constraints.</em></h1>
 <p className="lede">Explore how additional demand affects voltage, loading and contingency outcomes on standard CIGRE reference networks. Separate PyPSA scenarios illustrate regional assumptions; none represents an operator-calibrated connection study.</p>
 <div className="action-row"><Link href="/network-map" className="button">Explore 2024 OSM topology ↗</Link><a className="button secondary" target="_blank" rel="noreferrer" href={report.source_workflow_url}>Inspect numerical solver run ↗</a></div>
 </div></section>
 <section className="section"><div className="wrap"><EngineeringScenarioExplorer/></div></section>
 <section className="section compact"><div className="wrap"><div className="limit-box"><span className="kicker">Evidence boundary</span><p>CIGRE outcomes use reference engineering models only. PyPSA regional v2 uses source-checked Fingrid national data with hypothetical regional shares and line limits. The full OSM proxy is not an operator-calibrated 2025 Finnish network. The common 3-bus numerical comparison validates only that small explicitly matched reference. Actual site-connectable MW, queue position and regulatory feasibility remain unknown.</p></div></div></section>
 </>;
}