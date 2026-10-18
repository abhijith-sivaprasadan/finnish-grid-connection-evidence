"use client";
import {useEffect,useMemo,useState} from "react";
import {ArrowUpRight,Database,Activity,ShieldCheck,Clock3,ArrowRight,RefreshCw} from "lucide-react";
import {ResponsiveContainer,LineChart,Line,CartesianGrid,XAxis,YAxis,Tooltip} from "recharts";

type Point={connection_point_id:string;name:string;operator:string;voltage_kv:number;source_url:string};
type Capacity={observation_id:string;connection_point_id:string;name:string;direction:string;effective_year:number;capacity_value:number;capacity_unit:string;source_url:string;source_observed_at:string};
type Operation={source:string;dataset_id:string;metric:string;value:number;unit:string;timestamp_utc:string;interval_end_utc:string;retrieved_at:string;source_url:string};
type Envelope<T>={data:T[];meta:Record<string,unknown>};
const ROOT="https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence";
const SOURCE="https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/";
const NAV=[["#overview","Overview"],["#capacity","Capacity evidence"],["#system","System context"],["#methodology","Methodology"]];
function fmt(timestamp:string){const d=new Date(timestamp);return Number.isNaN(d.getTime())?"Unknown":d.toLocaleString("en-GB",{day:"2-digit",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit",timeZone:"UTC"})+" UTC";}
async function api<T>(url:string):Promise<Envelope<T>>{const r=await fetch(url);if(!r.ok)throw new Error("Source data is currently unavailable");return r.json();}
export default function Home(){
 const [points,setPoints]=useState<Point[]>([]);
 const [capacity,setCapacity]=useState<Capacity[]>([]);
 const [operations,setOperations]=useState<Operation[]>([]);
 const [loading,setLoading]=useState(true);
 const [error,setError]=useState("");
 const [direction,setDirection]=useState("production");
 const [year,setYear]=useState("2030");
 const [selected,setSelected]=useState("all");
 const [series,setSeries]=useState("fingrid:124");
 const [updated,setUpdated]=useState("");
 async function load(){
  setLoading(true);setError("");
  try{const [p,c,o]=await Promise.all([
   api<Point>("/api/v1/points"),api<Capacity>("/api/v1/capacity"),api<Operation>("/api/v1/operations?limit=2000")]);
   setPoints(p.data);setCapacity(c.data);setOperations(o.data);
   setUpdated(new Date().toISOString());
  }catch(e){setError(e instanceof Error?e.message:"Data unavailable");}
  finally{setLoading(false)}
 }
 useEffect(()=>{load();const id=setInterval(load,300000);return()=>clearInterval(id)},[]);
 const rows=useMemo(()=>points.filter(p=>selected==="all"||p.connection_point_id===selected).map(p=>{
  const v=capacity.filter(c=>c.connection_point_id===p.connection_point_id&&c.direction===direction&&String(c.effective_year)===year);
  return {p,observation:v.length===1?v[0]:null,ambiguous:v.length>1};
 }),[points,capacity,direction,year,selected]);
 const sourceChoices=useMemo(()=>Array.from(new Set(operations.map(o=>o.source+":"+o.dataset_id))),[operations]);
 const [provider,dataset]=series.split(":");
 const plotData=useMemo(()=>operations.filter(o=>o.source===provider&&o.dataset_id===dataset)
  .sort((a,b)=>a.timestamp_utc.localeCompare(b.timestamp_utc))
  .map(o=>({date:o.timestamp_utc,display:fmt(o.timestamp_utc),value:Number(o.value)})),[operations,provider,dataset]);
 const freshest=operations.map(o=>o.interval_end_utc).sort().at(-1);
 const lag=freshest?Math.max(0,Math.round((Date.now()-new Date(freshest).getTime())/3600000)):null;
 return <div className="site" id="overview">
 <header className="masthead"><a className="wordmark" href="#overview"><span className="logo">FG</span>finnish<b>grid</b>atlas</a><nav aria-label="Main navigation">{NAV.map(([href,text])=><a href={href} key={href}>{text}</a>)}</nav><a className="source-code" href={ROOT} target="_blank" rel="noreferrer">Source code <ArrowUpRight size={15}/></a></header>
 <main>
 <section className="hero"><div><div className="eyebrow">Independent research / Finland / Electricity networks</div><h1>Understanding the grid, <em>one piece of evidence at a time.</em></h1><p className="lead">Source-linked connection-capacity estimates and national power-system chronology, presented with the uncertainty and limits that real engineering decisions require.</p><div className="actions"><a className="primary" href="#capacity">Explore grid evidence <ArrowRight size={18}/></a><a href="#methodology" className="secondary">How to interpret this data</a></div></div><aside className="hero-aside"><div className="eyebrow">Research boundary / 01</div><h2>Indicative does not mean available.</h2><p>Published estimates are neither reserved connection capacity nor network study results. National load and production cannot establish local substation headroom.</p><span>Independent source re-verification pending</span></aside></section>
 <section className="numbers" aria-label="Evidence inventory"><div><strong>{loading?"—":points.length}</strong><span>Fingrid connection points</span></div><div><strong>{loading?"—":capacity.length}</strong><span>Indicative source records</span></div><div><strong>{loading?"—":operations.length}</strong><span>Recent operational records displayed</span></div><div><strong>{lag===null?"—":lag+" h"}</strong><span>Lag of latest source interval</span></div></section>
 {error&&<div role="alert" className="error"><ShieldCheck size={18}/>{error}. The interface does not fabricate measurements.</div>}
 <section className="section" id="capacity"><div className="section-heading"><div className="eyebrow">01 / Published connection evidence</div><h2>See what is published. <em>Keep the unknown visible.</em></h2><p>Compare production and consumption directions by the years explicitly represented in the captured Grid Scope sample. Missing observations are not zero capacity.</p></div>
 <div className="workbench"><div className="filters"><label>Direction<select value={direction} onChange={e=>setDirection(e.target.value)}><option value="production">Production</option><option value="consumption">Consumption</option></select></label><label>Published year<select value={year} onChange={e=>setYear(e.target.value)}>{["2026","2030","2035"].map(y=><option key={y}>{y}</option>)}</select></label><label>Connection point<select value={selected} onChange={e=>setSelected(e.target.value)}><option value="all">All recorded points</option>{points.map(p=><option key={p.connection_point_id} value={p.connection_point_id}>{p.name}</option>)}</select></label></div>
 <div className="table-wrap"><table><thead><tr><th>Connection point</th><th>Direction</th><th>Year</th><th>Source figure</th><th>Evidence</th></tr></thead><tbody>{rows.map(({p,observation,ambiguous})=><tr key={p.connection_point_id}><td><b>{p.name}</b><small>{p.voltage_kv} kV · {p.operator}</small></td><td>{direction}</td><td>{year}</td><td><b className={observation?"numeric":"muted"}>{observation?observation.capacity_value+" "+observation.capacity_unit:ambiguous?"Requires reconciliation":"Not recorded"}</b></td><td>{observation?<a target="_blank" rel="noreferrer" href={observation.source_url}>Indicative ↗</a>:<span className="muted">Unknown in snapshot</span>}</td></tr>)}</tbody></table>{!loading&&!rows.length&&<div className="empty">No observations for this selection.</div>}</div>
 <div className="workbench-bottom"><span><ShieldCheck size={16}/> 17 Oct 2026 source transcription · Not independently rechecked</span><a href={SOURCE} target="_blank" rel="noreferrer">View Fingrid Grid Scope <ArrowUpRight size={15}/></a></div></div></section>
 <section className="section" id="system"><div className="section-heading"><div className="eyebrow">02 / National operational chronology</div><h2>The system beyond <em>the individual connection.</em></h2><p>Authenticated Fingrid and ENTSO-E observations, presented as national operating context. Values retain the source metric, unit and UTC time interval.</p></div>
 <div className="chart-box"><div className="chart-bar"><div><div className="eyebrow">Measured / National / Time series</div><h3>Electricity operations</h3></div><label>Series<select value={sourceChoices.includes(series)?series:(sourceChoices[0]||series)} onChange={e=>setSeries(e.target.value)}>{sourceChoices.map(s=><option key={s} value={s}>{s.replace(":"," · Dataset ")}</option>)}</select></label></div>
 {plotData.length?<div className="chart-outer"><ResponsiveContainer width="100%" height={350}><LineChart data={plotData} margin={{top:15,right:20,left:0,bottom:15}}><CartesianGrid vertical={false} stroke="#e4dece"/><XAxis dataKey="display" tick={{fontSize:10}} minTickGap={55}/><YAxis tick={{fontSize:12}}/><Tooltip labelStyle={{color:"#143b30"}} contentStyle={{background:"#fffdf5",border:"1px solid #d4d0be"}}/><Line type="linear" dataKey="value" stroke="#20513d" strokeWidth={2.5} dot={false} isAnimationActive={false}/></LineChart></ResponsiveContainer></div>:<div className="empty">{loading?"Retrieving operational evidence…":"No persisted observations in this series."}</div>}
 <div className="chart-bottom"><span><Clock3 size={16}/> Newest stored source interval: {freshest?fmt(freshest):"Not available"}</span><span>Source intervals · not live SCADA</span></div></div></section>
 <section className="section" id="methodology"><div className="section-heading"><div className="eyebrow">03 / Research method and provenance</div><h2>A useful screening tool must also show <em>what it cannot prove.</em></h2></div><div className="cards"><article><Database size={22}/><small>Source separation</small><h3>One database. Distinct meanings.</h3><p>Capacity estimates and operational time series are stored in separate evidence categories. They must not be combined to invent a substation connection offer.</p></article><article><Activity size={22}/><small>Data chronology</small><h3>Historical, not instantaneous.</h3><p>Operational data updates asynchronously from operator publications. The latest source interval and its age are disclosed rather than claiming continuous telemetry.</p></article><article><ShieldCheck size={22}/><small>Verification boundary</small><h3>Transcribed ≠ independently validated.</h3><p>All 18 Grid Scope estimates remain subject to independent source-number verification. Publication year, direction and units are preserved.</p></article></div><div className="api-banner"><div><div className="eyebrow">For developers / v1</div><h3>Access the evidence through a REST API.</h3><p>Read-only JSON endpoints with bounded results, source timestamps and explicit uncertainty metadata. No source API keys in the browser.</p></div><a className="secondary" href="/api/v1">API reference <ArrowUpRight size={16}/></a></div></section>
 </main><footer><div><a className="wordmark" href="#overview"><span className="logo">FG</span>finnish<b>grid</b>atlas</a><p>Independent engineering research · not affiliated with Fingrid or ENTSO-E.</p></div><div><a href={ROOT} target="_blank" rel="noreferrer">Repository</a><a href="/api/v1">REST API</a><a href="https://kerala2040.github.io/" target="_blank" rel="noreferrer">Design lineage</a></div><small>{updated?"Last web check: "+fmt(updated):"Awaiting source check"} · Data remains source-controlled</small></footer></div>
}
