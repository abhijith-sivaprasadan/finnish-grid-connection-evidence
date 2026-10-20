/** Read-only source-evidence triage, NOT technical grid-connection feasibility. */
import type { Capacity, Point } from "./types";
import { BadInput } from "./params";
import { sourceReviewStatus, type ScreenshotStatus } from "./verification";

export type ScreeningInput={
 demand_mw:number; year:number; direction:"consumption"; voltage:"all"|110|220|400; connection_type:"switchyard"|"line"|"unspecified"
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
 connection_pathway:"nominal_switchyard_guidance_consistent"|"review_lower_voltage_switchyard"|
 "review_400kv_switchyard"|"line_220_400_prohibited"|"line_110_case_by_case"|
 "connection_type_unspecified"|"station_voltage_unknown";
 pathway_note:string; pathway_source_url:string;
 timing_evidence:"exact_year_capture"|"no_exact_year_capture";
 verified_reinforcement_for_this_point:false;
 next_actions:string[];
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
 "The 128-row historical designation list is an unscreened archive, not part of this five-point evidence sample.",
 "Fingrid standard switchyard voltage/power guidance is not an actual voltage-bay offer; a 400 kV labelled source point may have a separate 110/220 kV arrangement not represented in this five-point sample.",
 "No project-specific reinforcement, connection queue, commissioning permission or operator-approved voltage design is documented in this dataset."
];

export function parseScreening(q:URLSearchParams):ScreeningInput{
 for(const key of q.keys()){
  if(!["demand_mw","year","direction","voltage","connection_type"].includes(key))
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
 const connection_type=q.get("connection_type")??"switchyard";
 if(!["switchyard","line","unspecified"].includes(connection_type))
  throw new BadInput("connection_type","choose switchyard, line or unspecified");
 return {demand_mw,year,direction:"consumption",voltage:rawVoltage==="all"?"all":Number(rawVoltage) as 110|220|400,
 connection_type:connection_type as ScreeningInput["connection_type"]};
}

export const FINGRID_CONNECTION_PATHWAY_SOURCE="https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/";
/** Separate the source station voltage from the customer's *actual* planned bay.
 * This is a planning-rule prompt, NEVER operator confirmation of a connection.
 */
export function assessConnectionPathway(input:ScreeningInput, stationVoltage:number|null){
 const v=stationVoltage;
 const actions=["Ask Fingrid to assess exact site coordinates, load profile, commissioning date, connection configuration, grid queue and technical limits."];
 const result=(status:ScreeningRow["connection_pathway"],note:string)=>{
  const specific:string[]={
   review_lower_voltage_switchyard:["Ask Fingrid whether a 110/220 kV switchyard or appropriate transformer arrangement exists at/near the named source point; do not assume its 400 kV label is an available 400 kV project bay."],
   review_400kv_switchyard:["Ask Fingrid to assess a suitable 400 kV switchyard solution for the planned MW and commissioning timetable."],
   line_220_400_prohibited:["Remove the proposed direct 220/400 kV transmission-line connection and examine a switchyard alternative."],
   line_110_case_by_case:["Supply 110 kV line and transformer particulars for case-specific technical review; 40 MVA transformer limits cannot be inferred from the requested MW alone."],
   connection_type_unspecified:["Specify the proposed line or switchyard arrangement and confirm the candidate point's physical voltage levels."],
   station_voltage_unknown:["Obtain a source-backed voltage and connection arrangement before testing its applicable planning rules."],
   nominal_switchyard_guidance_consistent:["Request written Fingrid confirmation of equipment ratings, available circuit-breaker bays, system-security limits and point-specific connection terms."]
  }[status];
  return {connection_pathway:status,pathway_note:note,pathway_source_url:FINGRID_CONNECTION_PATHWAY_SOURCE,
          next_actions:[...specific,...actions]};
 };
 if(input.connection_type==="unspecified")
  return result("connection_type_unspecified","Select and verify a proposed switchyard or transmission-line connection before assuming a viable route.");
 if(v===null || ![110,220,400].includes(v))
  return result("station_voltage_unknown","No source-supported nominal switchyard voltage: obtain the operator's actual connection arrangement.");
 if(input.connection_type==="line"){
  if(v!==110)return result("line_220_400_prohibited","Fingrid does not permit direct 220/400 kV transmission-line connections for system-security reasons. Consider an operator-approved switchyard configuration.");
  return result("line_110_case_by_case","110 kV line connections are case-by-case and limited by technical criteria; the transformer nominal rating limit is 40 MVA, which is not directly interchangeable with MW.");
 }
 if(input.demand_mw<250 && v===400)
  return result("review_lower_voltage_switchyard","Fingrid's published standard switchyard range for less than 250 MW is 110/220 kV. A 400-kV-labelled station does not prove a suitable 110/220 kV bay exists.");
 if(input.demand_mw>=250 && v!==400)
  return result("review_400kv_switchyard","Fingrid's published standard switchyard range at 250 MW or more is 400 kV; do not assume this 110/220 kV point can serve the request.");
 return result("nominal_switchyard_guidance_consistent","The nominal station voltage and requested MW fit Fingrid's published switchyard planning range only. Feasibility, exact bay availability and network security remain unassessed.");
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
   feasibility:"not_assessed" as const,
   ...assessConnectionPathway(input,p.voltage_kv)
  };
  const blank=(status:EvidenceStatus):ScreeningRow=>({
   ...basic,
   next_actions:[...(status==="unknown_not_captured"?["Capture or recheck the exact requested year and consumption direction from Fingrid Grid Scope; do not substitute other years."]:["Resolve the missing, duplicate, or conflicting source snapshot before using its indicative MW." ]),...basic.next_actions],timing_evidence:"no_exact_year_capture",verified_reinforcement_for_this_point:false,
   evidence_status:status,capacity_value:null,capacity_unit:null,
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
   timing_evidence:"exact_year_capture" as const,verified_reinforcement_for_this_point:false as const,
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
