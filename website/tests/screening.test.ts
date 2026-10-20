import test from "node:test";
import assert from "node:assert/strict";
import {parseScreening,screenRecords} from "../src/lib/screening";
import {snapshotPoints,snapshotCapacities} from "../src/lib/snapshot";
import type {Capacity} from "../src/lib/types";
import {BadInput} from "../src/lib/params";

const inputs=parseScreening(new URLSearchParams("demand_mw=100&year=2030&direction=consumption&voltage=all"));
const pass=(_:Capacity)=>({status:"screenshot_match" as const,grade:"exact_tooltip" as const,review_date:"2026-10-19"});

test("only Seinäjoki and Uusnivala meet 2030 consumption pilot threshold",()=>{
 const s=screenRecords(snapshotPoints,snapshotCapacities,inputs);
 assert.equal(s.scope.total_catalogued_connection_points,5);
 assert.equal(s.scope.national_coverage,false);
 assert.equal(s.scope.archive_included,false);
 assert.equal(s.summary.indicative_threshold_met,2);
 assert.equal(s.summary.unknown_not_captured,3);
 assert.equal(s.summary.operator_confirmed_feasible,0);
 assert.equal(s.summary.feasibility_assessments_performed,0);
 assert.deepEqual(s.results.filter(r=>r.evidence_status==="indicative_threshold_met").map(r=>r.name).sort(),
  ["SEINÄJOKI 400 kV","UUSNIVALA 400 kV"]);
 assert.deepEqual(s.results.filter(r=>r.evidence_status==="unknown_not_captured").map(r=>r.name).sort(),
  ["ALAJÄRVI 400 kV","ALAPITKÄ 400 kV","VUOLIJOKI 400 kV"].sort());
 assert.ok(s.results.every(r=>r.feasibility==="not_assessed"));
});

test("production and 2026 consumption never fill missing 2030 consumption",()=>{
 const s=screenRecords(snapshotPoints,snapshotCapacities,inputs);
 const unknown=s.results.filter(r=>r.evidence_status==="unknown_not_captured");
 assert.equal(unknown.length,3);
 assert.ok(unknown.every(r=>r.capacity_value===null&&r.observation_id===null));
});

test("minimum threshold is inclusive, but below does not mean infeasible",()=>{
 const point=snapshotPoints[0];
 const original=snapshotCapacities.find(r=>r.connection_point_id===point.connection_point_id&&r.direction==="consumption")!;
 const obs:Capacity={...original,effective_year:2030,capacity_value:100,observation_id:"synthetic-review-fixture"};
 assert.equal(screenRecords([point],[obs],inputs,pass).results[0].evidence_status,"indicative_threshold_met");
 assert.equal(screenRecords([point],[{...obs,capacity_value:99}],inputs,pass).results[0].evidence_status,"indicative_below_request");
 assert.equal(screenRecords([point],[],inputs,pass).results[0].evidence_status,"unknown_not_captured");
});

test("MVA cannot masquerade as 100 MW",()=>{
 const obs:Capacity={...snapshotCapacities[0],capacity_unit:"MVA",direction:"consumption",effective_year:2030};
 const r=screenRecords([snapshotPoints[0]],[obs],inputs,pass).results[0];
 assert.equal(r.evidence_status,"unit_not_comparable");
 assert.equal(r.feasibility,"not_assessed");
});

test("newer unreviewed source cannot fall back to the older reviewed figure",()=>{
 const original=snapshotCapacities.find(o=>o.name==="UUSNIVALA 400 kV"&&o.effective_year===2030)!;
 const newer={...original,observation_id:"synthetic-newer-capture",capacity_value:500,source_observed_at:"2026-10-18T00:00:00Z"};
 const r=screenRecords([snapshotPoints[4]],[original,newer],inputs).results[0];
 assert.equal(r.evidence_status,"needs_source_review");
 assert.equal(r.capacity_value,500);
 assert.equal(r.source_review,"not_audited");
});

test("same-snapshot contradictory numeric values fail closed",()=>{
 const original=snapshotCapacities.find(o=>o.name==="SEINÄJOKI 400 kV"&&o.effective_year===2030)!;
 const changed={...original,observation_id:"synthetic-duplicate",capacity_value:700};
 const r=screenRecords([snapshotPoints[3]],[original,changed],inputs,pass).results[0];
 assert.equal(r.evidence_status,"conflicting_evidence");
 assert.equal(r.capacity_value,null);
});

test("unreviewed single observation cannot qualify as threshold met",()=>{
 const original=snapshotCapacities[0];
 const obs={...original,observation_id:"test-new",direction:"consumption" as const,effective_year:2030,capacity_value:800};
 const r=screenRecords([snapshotPoints[0]],[obs],inputs).results[0];
 assert.equal(r.evidence_status,"needs_source_review");
});

test("voltage is sample-only filter, not an assertion of national 110 kV coverage",()=>{
 const crit=parseScreening(new URLSearchParams("voltage=110"));
 const s=screenRecords(snapshotPoints,snapshotCapacities,crit);
 assert.equal(s.scope.sampled_connection_points,0);
 assert.equal(s.scope.total_catalogued_connection_points,5);
 assert.equal(s.scope.national_coverage,false);
});

test("strict input schema refuses duplication and invalid direction and demand",()=>{
 for(const q of ["demand_mw=0","demand_mw=-5","demand_mw=10001","demand_mw=Infinity",
  "year=2032&direction=production","voltage=99","demand_mw=100&demand_mw=400",
  "extra=ignored","year=2O30"]){
   assert.throws(()=>parseScreening(new URLSearchParams(q)),BadInput,q);
 }
});

test("Fingrid 250 MW switchyard guidance is separate from source threshold",()=>{
 const s=screenRecords(snapshotPoints,snapshotCapacities,inputs);
 const matched=s.results.filter(x=>x.evidence_status==="indicative_threshold_met");
 assert.equal(matched.length,2);
 assert.ok(matched.every(x=>x.connection_pathway==="review_lower_voltage_switchyard"));
 assert.ok(matched.every(x=>x.verified_reinforcement_for_this_point===false));
 assert.ok(matched.every(x=>x.feasibility==="not_assessed"));
 assert.ok(matched.every(x=>x.pathway_source_url.startsWith("https://www.fingrid.fi/")));
});

test("exact 250 MW boundary, below threshold and suggested switchyard voltages",()=>{
 const high=screenRecords(snapshotPoints,snapshotCapacities,parseScreening(new URLSearchParams("demand_mw=250")));
 assert.ok(high.results.every(x=>x.connection_pathway==="nominal_switchyard_guidance_consistent"));
 const low=screenRecords(snapshotPoints,snapshotCapacities,parseScreening(new URLSearchParams("demand_mw=249.999")));
 assert.ok(low.results.every(x=>x.connection_pathway==="review_lower_voltage_switchyard"));
});

test("no direct 220/400 kV line connection; no 110 kV blanket line permission",()=>{
 const line=parseScreening(new URLSearchParams("demand_mw=100&connection_type=line"));
 const p=screenRecords(snapshotPoints,snapshotCapacities,line);
 assert.ok(p.results.every(x=>x.connection_pathway==="line_220_400_prohibited"));
 const virtualPoint={...snapshotPoints[0],voltage_kv:110};
 const p110=screenRecords([virtualPoint],[],line);
 assert.equal(p110.results[0].connection_pathway,"line_110_case_by_case");
 assert.match(p110.results[0].pathway_note,/40 MVA/);
 const undecided=parseScreening(new URLSearchParams("connection_type=unspecified"));
 assert.equal(screenRecords(snapshotPoints,snapshotCapacities,undecided).results[0].connection_pathway,"connection_type_unspecified");
});

test("reject unsupported connection types and repeated query controls",()=>{
 for(const q of ["connection_type=110","connection_type=switchyard&connection_type=line"]){
  assert.throws(()=>parseScreening(new URLSearchParams(q)),BadInput);
 }
});
