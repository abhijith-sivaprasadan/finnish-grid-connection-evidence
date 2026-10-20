import type {Metadata} from "next";
import Link from "next/link";
import model from "@/lib/pypsa-zonal-2025.json";
export const metadata:Metadata={title:"Conditional Swedish–Finnish market corridor model | Grid Atlas"};
const fmt=(n:number)=>n.toLocaleString("en-US",{maximumFractionDigits:1});
export default function MarketCorridors2025(){
 return <section className="vse-page">
  <header className="vse-hero"><p className="vse-kicker">AUDITED FINGRID 2025 / THREE ABSTRACT MARKET ZONES</p>
   <h1>Two separate market corridors, <em>not a physical power grid.</em></h1>
   <p>A verified 24-scenario PyPSA/HiGHS sensitivity with independent, actual 15-minute Swedish SE1 and SE3 remaining intraday market capacity bounds into Finland. Designed to expose corridor reliance and assumptions—not to certify connection headroom.</p>
   <div className="vse-hero-metrics"><span>2 authentic source-capped links</span><span>2,880 quarter-hours</span><span>24 optimal scenarios</span></div>
  </header>
  <div className="vse-caveat"><strong>No physical-grid claim.</strong> The SE1 and SE3 connections here are independently capped <em>commercial trading links</em>, not real thermal ratings, line impedances or Finnish substations. The fictitious project can access them only under our assumed market-delivery conditions.</div>
  <section className="vse-panel"><p className="vse-kicker">01 / OPERATOR EVIDENCE PER BORDER</p><h2>Two observed independent market constraints</h2>
   <div className="vse-overview">{model.edge_constraints.map(c=><div key={c.edge}><small>{c.edge} · Fingrid #{c.fingrid_dataset_id}</small><strong>{fmt(c.median_mw)} MW</strong><span>Median original unused intraday capacity; maximum {fmt(c.max_mw)} MW. Not physical headroom.</span></div>)}</div>
   <p className="vse-note">Actual source observations were collected from <a href="https://data.fingrid.fi/en/datasets/38">Fingrid 38</a> and <a href="https://data.fingrid.fi/en/datasets/39">Fingrid 39</a>. The 30-day study reuses previously validated source hashes without additional operator requests. Separate historical commercial trade flows 31 and 32 are not identical to physical power transfers.</p>
  </section>
  <section className="vse-panel"><p className="vse-kicker">02 / VERIFIED CONDITIONAL CASES</p><h2>What happens when one of the two trading corridors is unavailable?</h2>
   <p className="vse-note">24 optimal PyPSA scenarios: both corridors available, only SE1 or only SE3; hypothetical firm or hindsight flexible ±50 MW demand; optional 100 MW battery for 2/4/8 hours at 90% assumed round-trip efficiency. The result is <strong>model penalty relaxation</strong>, not recorded unserved electricity.</p>
   <div className="vse-table-overflow"><table className="vse-table"><thead><tr><th>Assumed access</th><th>100 MW load</th><th>Battery</th><th>Conditional penalty relaxation</th></tr></thead>
    <tbody>{model.scenarios.map((r,i)=><tr key={i}><td>{r.corridors_allowed.replaceAll("_"," ")}</td><td>{r.flex_half_span_mw_assumed===0?"Firm":"Hindsight ±50 MW"}</td><td>{r.battery_duration_hours_assumed===0?"None":r.battery_duration_hours_assumed+" hours"}</td><td>{fmt(r.modelled_project_relaxation_mwh)} MWh</td></tr>)}</tbody></table></div>
   <p className="vse-note">Swedish supply is model-assumed behind both borders; equal-cost allocation is not operator-measured. Keeping both corridors cannot worsen the optimum versus removing one under otherwise identical assumptions. The report verifies every link's 15-minute original capacity and FI project balance.</p>
   <a href={model.source_run} target="_blank" rel="noreferrer">Original fingerprints, 3-bus network code and 24 optimal-case solver report ↗</a>
  </section>
  <section className="vse-panel vse-limitations"><p className="vse-kicker">03 / PHYSICAL-GRID LIMITATIONS</p><h2>What still needs operator electrical network evidence?</h2>
   {model.limitations.map((x,i)=><p key={i}>{x}</p>)}
   <p>Fingrid's <a href="https://data.fingrid.fi/en/datasets/30">P1 north–south measured flow</a> is a separate one-minute historical physical transfer record; its historical weekly directional capacity datasets <a href="https://data.fingrid.fi/en/datasets/28">28</a>/<a href="https://data.fingrid.fi/en/datasets/29">29</a> are marked ended. They must not be treated as verified contemporaneous 2025 15-minute thermal ratings without a fresh source completeness and frequency audit.</p>
   <Link href="/analysis/borders-2025">Back to historical Swedish-border evidence ↗</Link>
  </section>
 </section>;
}
