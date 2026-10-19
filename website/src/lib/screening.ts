/** Read-only source-evidence triage, NOT technical grid-connection feasibility. */
import type { Capacity, Point } from "./types";
import { BadInput } from "./params";
import { sourceReviewStatus, type ScreenshotStatus } from "./verification";

export type ScreeningInput={
 demand_mw:number; year:number; direction:"consumption"; voltage:"all"|110|220|400
};
export type EvidenceStatus=
 "indicative_threshold_met"|"indicative_below_request"|
 "unknown_not_captured"|"needs_source_review"|
 "conflicting_evidence"|"unit_not_comparable";
export type ScreeningRow={
 connection_point_id:string;name:string;operator:string;voltage_kv:number|null;
 evidence_status:EvidenceStatus; feasibility:"not_assessed";
 capacity_value:number|null;capacity_unit:"MW"|"MVA"|null;
 observation_id:string|null;source_url:string|null;source_observed_at:string|null;
 validity_notes:string|null;source_review:"screenshot_match"|"not_audited"|"none";
 source_review_grade:string|null;source_review_date:string|null;
 evidence_count:number;
};
const statuses:EvidenceStatus[]=[
 "indicative_threshold_met","indicative_below_request","unknown_not_captured",
 "needs_source_review","conflicting_evidence","unit_not_comparable"
];
const caution=[
 "Screening ranks source evidence for further research only; it does not establish physical feasibility, a connection offer, grid studies, queue position or connection rights.",
 "Fingrid Grid Scope provides conditional indicative estimates for selected substations, not guaranteed capacity.",
 "Unknown means not captured in the research sample; it never means zero or physically infeasible.",
 "Do not interpolate between effective years, substitute production for consumption, convert MVA to MW without documented assumptions, subtract demand to claim spare MW, or add across connection points.",
 "The 128-row historical designation list is an unscreened archive, not part of this five-point evidence sample."
];

export function parseScreening(q:URLSearchParams):ScreeningInput{
 for(const key of q.keys()){
  if(!["demand_mw","year","direction","voltage"].includes(key))
   throw new BadInput(key,"unrecognized screening parameter");
  if(q.getAll(key).length!==1)throw new BadInput(key,"duplicate parameter");
 }
 const demand=q.get("demand_mw")??"100";
 if(!/^(?:\d+(?:\.\d+)?|\.\d+)$/.test(demand))throw new BadInput("demand_mw","must be a positive MW number");
 const demand_mw=Number(demand);
 if(!Number.isFinite(demand_mw)||demand_mw<=0||demand_mw>10000)
   throw new BadInput("demand_mw","must be greater than zero and at most 10,000 MW");
 const rawYear=q.get("year")??"2030";
 if(!/^\d{4}$/.test(rawYear))throw new BadInput("year","must be four digits");
 const year=Number(rawYear);
 if(year<1900||year>2200)throw new BadInput("year","outside documented schema range");
 const direction=q.get("direction")??"consumption";
 if(direction!=="consumption")throw new BadInput("direction","consumption only in screening v1");
 const rawVoltage=q.get("voltage")??"all";
 if(!["all","110","220","400"].includes(rawVoltage))
  throw new BadInput("voltage","choose all, 110, 220 or 400");
 return {demand_mw,year,direction:"consumption",voltage:rawVoltage==="all"?"all":Number(rawVoltage) as 110|220|400};
}

type ReviewFn=(observation:Capacity)=>ScreenshotStatus;
const marker=(row:Capacity)=>String(row.capacity_value)+"|"+row.capacity_unit+"|"+row.source_url;
/** Never choose a favorable value from contradictory or unreviewed snapshots. */
export function screenRecords(
 points:readonly Point[], observations:readonly Capacity[], input:ScreeningInput,
 review:ReviewFn=sourceReviewStatus
){
 const selected=points.filter(p=>input.voltage==="all"||p.voltage_kv===input.voltage)
  .slice().sort((a,b)=>a.name.localeCompare(b.name,"fi")||
   a.connection_point_id.localeCompare(b.connection_point_id));
 const rows:ScreeningRow[]=selected.map(p=>{
  const evidence=observations.filter(o=>o.connection_point_id===p.connection_point_id&&
   o.direction===input.direction&&o.effective_year===input.year&&
   o.capacity_status==="published_indicative");
  const basic={
   connection_point_id:p.connection_point_id,name:p.name,operator:p.operator,voltage_kv:p.voltage_kv,
   feasibility:"not_assessed" as const
  };
  const blank=(status:EvidenceStatus):ScreeningRow=>({
   ...basic,evidence_status:status,capacity_value:null,capacity_unit:null,
   observation_id:null,source_url:null,source_observed_at:null,validity_notes:null,
   source_review:"none",source_review_grade:null,source_review_date:null,evidence_count:evidence.length
  });
  if(evidence.length===0)return blank("unknown_not_captured");
  // A later recorded capture takes precedence even when it has NOT been reviewed.
  // Explicitly requiring recheck prevents favorable older values from winning.
  const sorted=evidence.slice().sort((a,b)=>{
   const da=Date.parse(a.source_observed_at),db=Date.parse(b.source_observed_at);
   return (Number.isFinite(db)?db:-Infinity)-(Number.isFinite(da)?da:-Infinity);
  });
  const freshest=sorted[0];
  const captured=Date.parse(freshest.source_observed_at);
  if(!Number.isFinite(captured))return blank("needs_source_review");
  const same=sorted.filter(o=>Date.parse(o.source_observed_at)===captured);
  if(same.length>1){
   const different=new Set(same.map(marker)).size>1;
   return blank(different?"conflicting_evidence":"needs_source_review");
  }
  const grade=review(freshest);
  const source={
   ...basic,
   observation_id:freshest.observation_id,
   source_url:freshest.source_url,
   source_observed_at:freshest.source_observed_at,
   validity_notes:freshest.validity_notes,
   source_review:grade.status,
   source_review_grade:grade.grade,
   source_review_date:grade.review_date,
   capacity_value:Number(freshest.capacity_value),
   capacity_unit:freshest.capacity_unit,
   evidence_count:evidence.length
  };
  if(grade.status!=="screenshot_match")return {...source,evidence_status:"needs_source_review" as const};
  if(freshest.capacity_unit!=="MW")return {...source,evidence_status:"unit_not_comparable" as const};
  if(!Number.isFinite(source.capacity_value)||source.capacity_value<0)
   return {...source,evidence_status:"needs_source_review" as const};
  return {...source,evidence_status:(source.capacity_value>=input.demand_mw?
   "indicative_threshold_met":"indicative_below_request") as EvidenceStatus};
 });
 const summary=Object.fromEntries(statuses.map(s=>[s,rows.filter(r=>r.evidence_status===s).length])) as Record<EvidenceStatus,number>;
 return {
  scenario:input,
  scope:{
   sampled_connection_points:rows.length,
   total_catalogued_connection_points:points.length,
   national_coverage:false,
   archive_included:false,
   observation_snapshot_dates:Array.from(new Set(rows.map(r=>r.source_observed_at).filter((t):t is string=>!!t))).sort()
  },
  summary:{...summary,operator_confirmed_feasible:0,feasibility_assessments_performed:0},
  results:rows, limitations:caution,
  interpretation:"Evidence-only screening. Indicative threshold met is NOT technically feasible or operator confirmed."
 };
}
