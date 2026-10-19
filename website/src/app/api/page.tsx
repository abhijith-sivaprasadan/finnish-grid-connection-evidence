import type { Metadata } from "next";
export const metadata:Metadata={title:"REST API"};
const endpoints=[
 ["GET","/api/v1/health","Database health; 200 or 503"],
 ["GET","/api/v1/overview","Stored evidence counters and source freshness"],
 ["GET","/api/v1/screening?demand_mw=100&year=2030&direction=consumption&voltage=all","Evidence-only 100 MW / 2030 screening; no feasibility conclusion"],
 ["GET","/api/v1/points","Paginated list of sampled connection points"],
 ["GET","/api/v1/stations?voltage=220","Historical main-grid designation archive (2020 table label); archived identity only, no MW"],
 ["GET","/api/v1/points/FI-FINGRID-ALAPITKA-400","One sampled point"],
 ["GET","/api/v1/capacity?direction=production&year=2030","Filtered published indicative estimates"],
 ["GET","/api/v1/coverage","Observed versus missing-in-compiled-capture combinations"],
 ["GET","/api/v1/quality","30-day source completeness and interval revisions"],
 ["GET","/api/v1/source-review","Original 18-row screenshot matches; no guaranteed headroom"],
 ["GET","/api/v1/export/recheck","CSV worksheet for independently reviewing 18 source transcriptions"],
 ["GET","/api/v1/operations?source=fingrid&dataset_id=124","National operational intervals; paginated, timezone-aware"],
 ["GET","/api/openapi.json","OpenAPI 3.1 schema"],
];
export default function API(){return <><section className="page-hero"><div className="wrap">
 <p className="eyebrow">04 / Public developer interface</p>
 <h1>A real, read-only <em>REST API.</em></h1>
 <p className="lede">Source-traceable JSON endpoints, bounded pagination, validated query parameters and explicit scientific caveats. No browser-side credentials.</p>
 </div></section><section className="section compact"><div className="wrap">
 <div className="notice">Version 1 · GET only · JSON · No write endpoints. The archived station-list endpoint is an attributed static historical-source record. The point and capacity routes use a clearly identified public snapshot if Neon is not configured. Operational data require the live evidence store, and database health returns 503 without it.</div>
 <div className="section-intro table-heading"><p className="eyebrow">Reference</p><h2>Explore documented endpoints.</h2></div>
 <div className="table-wrap"><table><thead><tr><th>Method</th><th>Endpoint</th><th>Purpose</th></tr></thead><tbody>
 {endpoints.map(([method,path,description])=><tr key={path}><td className="mono">{method}</td><td><a className="mono url" href={path}>{path} ↗</a></td><td>{description}</td></tr>)}
 </tbody></table></div>
 <div className="grid-2 panels">
 <article className="research-card"><span className="kicker">Filters</span><h3>Predictable query semantics</h3>
 <p><code>limit</code> (1–500 depending on endpoint), <code>offset</code> (0–100000),
 <code>direction</code>, <code>point_id</code>, <code>year</code>, <code>voltage</code> (archival stations only),
 <code>source</code>, <code>dataset_id</code>, and ISO timestamps with explicit timezone.
 Invalid values receive HTTP 400 rather than unbounded database scans.</p></article>
 <article className="research-card"><span className="kicker">Operational safety</span><h3>Public read endpoints only</h3>
 <p>Successful responses expose provenance and explicit limitations.
 Data-store failures return HTTP 503 without leaking provider keys,
 database error messages or connection strings. Live database access requires the
 existing <code>grid_dashboard_reader</code> PostgreSQL role.</p></article></div>
 <div className="limit-box"><span className="kicker">Scientific interpretation</span>
 <p>A REST endpoint does not turn a manually transcribed estimate into an independently validated quantity.
 Capacity observations are conditional, spatially interdependent and not additive. National operations are a separate evidence category. Historical substation names establish neither current operational status nor connectability.</p></div>
 </div></section></>}
