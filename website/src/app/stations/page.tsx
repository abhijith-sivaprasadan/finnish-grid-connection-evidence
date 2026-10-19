import type { Metadata } from "next";
import Link from "next/link";
import { StationInventoryExplorer } from "@/components/station-inventory-explorer";
import official from "@/lib/main-grid-designation.json";

export const metadata:Metadata={title:"Historical main-grid station inventory"};
export default function StationsPage(){
 return <><section className="page-hero"><div className="wrap">
  <p className="eyebrow">04 / Source-backed historical designation</p>
  <h1>Station <em>inventory.</em></h1>
  <p className="lede">Search substations named in an operator-published designation appendix. This is a historical source inventory—not a live map, not a current national registry, and not a connection-capacity estimate.</p>
 </div></section>
 <section className="section compact"><div className="wrap">
  <div className="si-context" role="note"><strong>Which period does this represent?</strong>
   <p>The document is linked to Fingrid’s 2024 designation decision, but its substation table itself reads <b>Kantaverkko 1.1.2020</b>. The table lists <b>128 name–voltage rows</b> while its printed subtotal says <b>127</b>. We show all source rows and preserve that discrepancy. This must not be compared directly against Fingrid’s separate 2025 statistic of 138 main-grid substations.</p>
   <a target="_blank" rel="noreferrer" href={official.source_url}>Open the original 13-page Fingrid annex ↗</a>
  </div>
  <StationInventoryExplorer rows={official.rows}/>
  <div className="si-research-boundary"><div><h2>What the archive does not tell us</h2><p>Station ownership can be shared or limited to particular equipment. The document does not establish present-day operation, geographic coordinates, available MW, grid topology, customer queue position or connection rights. At least some listed sites are series-compensation stations rather than standard transformer substations.</p></div><div>
   <h2>Compare the right datasets</h2><p>Capacity estimates exist in a separate, much smaller Grid Scope capture: five named 400-kV connection points and 18 screenshot-matched values. Historical names alone are not capacity observations.</p><Link href="/connections">Open recorded Grid Scope values →</Link></div></div>
  <p className="chart-caption">Source: Fingrid 2024 designation appendix, station table caption 1.1.2020. This is an independently structured transcription, not an official Fingrid API or endorsed product. <Link href="/method">Methodology</Link> · <Link href="/api/v1/stations">Source-attributed JSON</Link></p>
 </div></section></>;
}
