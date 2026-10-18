import type { Metadata } from "next";
import { capacities, coverage, points } from "@/lib/repository";
import { BadInput } from "@/lib/params";
import Link from "next/link";
export const dynamic="force-dynamic";
export const metadata:Metadata={title:"Connection outlook"};
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
  let catalog:Awaited<ReturnType<typeof points>>["data"]=[];
  try {
    const [d,s,p]=await Promise.all([capacities(q),coverage(),points(new URLSearchParams("limit=100"))]);
    data=d;stats=s;catalog=p.data;
  } catch(error) {
    fault=error instanceof BadInput ? "A query filter is invalid; use the form below." :
      "The read-only database is temporarily unavailable. No values have been substituted.";
  }
  return <><section className="page-hero"><div className="wrap">
    <p className="eyebrow">01 / Source-transcribed connection capacity</p>
    <h1>Connection <em>outlook.</em></h1><p className="lede">Explore only the years and directions
    Fingrid Grid Scope was recorded as publishing for this small sample. Not a feasibility determination.</p>
  </div></section>
  <section className="section compact"><div className="wrap">
    <form method="get" action="/connections" className="filters" aria-label="Capacity filters">
      <label>Substation<select name="point_id" defaultValue={typeof inputs.point_id==="string"?inputs.point_id:""}>
        <option value="">All five points</option>
        {catalog.map(p=><option key={p.connection_point_id} value={p.connection_point_id}>{p.name}</option>)}
      </select></label>
      <label>Direction<select name="direction" defaultValue={typeof inputs.direction==="string"?inputs.direction:""}>
        <option value="">Both directions</option><option value="production">Production</option><option value="consumption">Consumption</option>
      </select></label>
      <label>Published effective year<select name="year" defaultValue={typeof inputs.year==="string"?inputs.year:""}>
        <option value="">All recorded years</option><option value="2026">2026</option>
        <option value="2030">2030</option><option value="2035">2035</option>
      </select></label><button className="button" type="submit">Apply filters →</button>
    </form>
    {fault&&<p role="alert" className="notice warn">{fault}</p>}
    {data?.data_mode==="compiled_snapshot"&&<p role="status" className="notice warn">Offline evidence mode: 18 indicative values transcribed from Fingrid Grid Scope on 17 October 2026. Source captures are not independently rechecked or live connection offers. National operations require a database connection.</p>}
    {stats&&<div className="data-strip three">
      <div><strong>{stats.coverage.published}</strong><span>Published source intersections</span></div>
      <div><strong>{stats.coverage.missing_in_compiled_capture}</strong><span>Missing in this compiled capture · not zero</span></div>
      <div><strong>{stats.coverage.needs_reconciliation}</strong><span>Records needing source reconciliation</span></div>
    </div>}
    <p className="source-note">An empty table cell means the selected snapshot has no recorded value—not that the operator reports zero megawatts. Connection points and years cannot be summed or interpolated.</p>
    <div className="section-intro table-heading"><p className="eyebrow">Source records</p><h2>Figures, with the original context.</h2><p>Filtered {data?.pagination.total ?? "—"} records. Each row retains a source link and capture timestamp.</p></div>
    {data&&<p className="results-actions"><Link href={"/api/v1/capacity?" + q.toString()} className="button secondary">Open filtered API JSON ↗</Link></p>}
    {data&&<div className="table-wrap"><table><thead><tr><th>Substation</th><th>Direction</th><th>Year</th><th>Indicative value</th><th>Source capture (UTC)</th><th>Evidence</th></tr></thead>
    <tbody>{data.data.map(o=><tr key={o.observation_id}><td><strong>{o.name}</strong></td><td>{o.direction}</td><td>{o.effective_year??"—"}</td>
      <td className="value-cell">{o.capacity_value} {o.capacity_unit}</td><td>{new Date(o.source_observed_at).toISOString().slice(0,16).replace("T"," ")}</td>
      <td><a href={o.source_url} target="_blank" rel="noreferrer">Operator source ↗</a></td></tr>)}</tbody></table></div>}
    {data&&data.data.length===0&&<p className="notice">No recorded observations match these filters. This does not imply zero capacity.</p>}
    <div className="limit-box"><span className="kicker">Required interpretation</span><p>
      These 18 source-transcribed Grid Scope figures still require an independent numeric recheck.
      They are not guaranteed connection rights or operator-confirmed available capacity.
      Selected sample observations do not characterize all Finnish substations.</p></div>
  </div></section></>;
}
