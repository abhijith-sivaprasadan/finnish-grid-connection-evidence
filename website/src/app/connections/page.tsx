import type { Metadata } from "next";
import { capacities, coverage } from "@/lib/repository";
import { evidenceCatalogue } from "@/lib/catalogue";
import { BadInput } from "@/lib/params";
import Link from "next/link";
import { ConnectionWorkbench } from "@/components/connection-workbench";
import type { Capacity, Point } from "@/lib/types";
import { sourceReviewStatus } from "@/lib/verification";
export const dynamic="force-dynamic";
export const metadata:Metadata={title:"Substation source evidence"};
type SP=Promise<Record<string,string|string[]|undefined>>;
export default async function Connections({searchParams}:{searchParams:SP}){
  const inputs=await searchParams;
  const q=new URLSearchParams();
  for(const key of ["direction","year","point_id"]) {
    const v=inputs[key];
    if(typeof v==="string"&&v)q.set(key,v);
  }
  q.set("limit","200");
  let fault:string|null=null;
  let data:Awaited<ReturnType<typeof capacities>>|null=null;
  let stats:Awaited<ReturnType<typeof coverage>>|null=null;
  let catalog:Point[]=[];
  let allObservations:Capacity[]=[];
  try {
    const [d,s,all]=await Promise.all([capacities(q),coverage(),evidenceCatalogue()]);
    data=d;stats=s;catalog=all.stations;allObservations=all.observations;
  } catch(error) {
    fault=error instanceof BadInput ? "A query filter is invalid; use the form below." :
      "The read-only database is temporarily unavailable. No values have been substituted.";
  }
  return <><section className="page-hero"><div className="wrap">
    <p className="eyebrow">01 / Substation evidence explorer</p>
    <h1>Connection <em>evidence.</em></h1><p className="lede">Browse actual captured point, direction and year values. Inspect the underlying source, find collection gaps and export recorded observations. Not a national substation catalogue or a feasibility determination.</p>
  </div></section>
  <section className="section compact"><div className="wrap">
    {catalog.length>0&&<ConnectionWorkbench points={catalog} observations={allObservations} initialPointId={typeof inputs.point_id==="string"?inputs.point_id:undefined}/>}
    <div className="section-intro table-heading" style={{marginTop:36}}><p className="eyebrow">RAW SOURCE LEDGER</p><h2>Trace individual records</h2><p>Filter the original source observations by station, direction and published effective year.</p></div>
    <form method="get" action="/connections" className="filters" aria-label="Capacity filters">
      <label>Substation<select name="point_id" defaultValue={typeof inputs.point_id==="string"?inputs.point_id:""}>
        <option value="">All catalogue points</option>
        {catalog.map(p=><option key={p.connection_point_id} value={p.connection_point_id}>{p.name}</option>)}
      </select></label>
      <label>Direction<select name="direction" defaultValue={typeof inputs.direction==="string"?inputs.direction:""}>
        <option value="">Both directions</option><option value="production">Production</option><option value="consumption">Consumption</option>
      </select></label>
      <label>Published effective year<select name="year" defaultValue={typeof inputs.year==="string"?inputs.year:""}>
        <option value="">All recorded years</option>
        {Array.from(new Set(allObservations.map(o=>o.effective_year).filter((y):y is number=>y!==null))).sort((a,b)=>a-b).map(y=><option key={y} value={y}>{y}</option>)}
      </select></label><button className="button" type="submit">Apply filters →</button>
    </form>
    {fault&&<p role="alert" className="notice warn">{fault}</p>}
    {data?.data_mode==="compiled_snapshot"&&<p role="status" className="notice warn">Offline evidence mode: 18 indicative values transcribed from Fingrid Grid Scope on 17 October 2026. The original 18 values matched reviewer-supplied screenshots; these are not live connection offers. National operations require a database connection.</p>}
    {stats&&<div className="data-strip three">
      <div><strong>{stats.coverage.published}</strong><span>Published source intersections</span></div>
      <div><strong>{stats.coverage.missing_in_compiled_capture}</strong><span>Missing in this compiled capture · not zero</span></div>
      <div><strong>{stats.coverage.needs_reconciliation}</strong><span>Records needing source reconciliation</span></div>
    </div>}
    <p className="source-note">An empty table cell means the selected snapshot has no recorded value—not that the operator reports zero megawatts. Connection points and years cannot be summed or interpolated.</p>
    <div className="section-intro table-heading"><p className="eyebrow">Source records</p><h2>Figures, with the original context.</h2><p>Filtered {data?.pagination.total ?? "—"} records. Each row retains a source link and capture timestamp.</p></div>
    {data&&<p className="results-actions"><Link href={"/api/v1/capacity?" + q.toString()} className="button secondary">Open filtered API JSON ↗</Link></p>}
    {data&&<div className="table-wrap"><table><thead><tr><th>Substation</th><th>Direction</th><th>Year</th><th>Indicative value</th><th>Source capture (UTC)</th><th>Source review</th><th>Evidence</th></tr></thead>
    <tbody>{data.data.map(o=><tr key={o.observation_id}><td><strong>{o.name}</strong></td><td>{o.direction}</td><td>{o.effective_year??"—"}</td>
      <td className="value-cell">{o.capacity_value} {o.capacity_unit}</td><td>{new Date(o.source_observed_at).toISOString().slice(0,16).replace("T"," ")}</td>
      <td>{sourceReviewStatus(o).status==="screenshot_match"?(sourceReviewStatus(o).grade==="exact_tooltip"?"Exact tooltip":"Panel MW"):"Not audited"}</td>
      <td><a href={o.source_url} target="_blank" rel="noreferrer">Operator source ↗</a></td></tr>)}</tbody></table></div>}
    {data&&data.data.length===0&&<p className="notice">No recorded observations match these filters. This does not imply zero capacity.</p>}
    <div className="limit-box"><span className="kicker">Required interpretation</span><p>
      The 18 original Grid Scope values matched reviewer-supplied screenshots (17 tooltips and one panel number); this is not physical grid validation.
      They are not guaranteed connection rights or operator-confirmed available capacity.
      This sampled catalogue does not characterize all Finnish substations.</p></div>
  </div></section></>;
}
