import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {snapshotPoints,snapshotCapacities} from "../src/lib/snapshot";
import {screenRecords,parseScreening} from "../src/lib/screening";

const read=(name:string)=>readFileSync(name,"utf8");

test("default case screen in public MVP derives real source counts and retains non-approval",()=>{
 const request=parseScreening(new URLSearchParams("demand_mw=100&year=2030&direction=consumption&connection_type=switchyard"));
 const report=screenRecords(snapshotPoints,snapshotCapacities,request);
 assert.equal(report.summary.indicative_threshold_met,2);
 assert.equal(report.summary.unknown_not_captured,3);
 assert.equal(report.summary.operator_confirmed_feasible,0);
 assert.ok(report.results.every(r=>r.feasibility==="not_assessed"));
 const home=read("src/app/page.tsx");
 assert.match(home,/screenRecords\(points,capacities/);
 assert.match(home,/screen.summary.indicative_threshold_met/);
 assert.match(home,/screen.summary.unknown_not_captured/);
 assert.match(home,/screen.summary.operator_confirmed_feasible/);
 assert.match(home,/overview\(\)/);
 assert.match(home,/evidenceCatalogue\(\)/);
});
test("public evidence coverage matrix maps only observed point, year and direction cells",()=>{
 assert.equal(snapshotPoints.length,5);
 assert.equal(snapshotCapacities.length,18);
 assert.equal(snapshotCapacities.length,new Set(snapshotCapacities.map(r=>
  [r.connection_point_id,r.effective_year,r.direction].join("|"))).size);
 const yearCount=new Set(snapshotCapacities.map(x=>x.effective_year)).size;
 assert.equal(snapshotPoints.length*yearCount*2-snapshotCapacities.length,12);
 const ui=read("src/components/evidence-matrix.tsx");
 for(const fragment of ["sourceReviewStatus","source_url","source_observed_at","effective_year",
  "point.connection_point_id","aria-pressed","aria-live","Not captured","no matching value","No matching value"]){
  assert.ok(ui.includes(fragment),fragment);
 }
 assert.doesNotMatch(ui,/operator_confirmed_feasible:\s*[1-9]/);
});
test("scoped engineering families can be selected but are not summed as one grid",()=>{
 const s=read("src/components/engineering-scenario-explorer.tsx");
 for(const family of ["hv","mv","regional","ac","osm"]){
  assert.ok(s.includes('study==="'+family+'"'),family);
 }
 assert.match(s,/aria-pressed/);
 assert.match(s,/CIGRE/);
 assert.match(s,/not actual Fingrid|not operator|not a Finnish|not a Fingrid/i);
});
test("screening and geographic map keep separate identities and source disclaimers",()=>{
 const home=read("src/app/page.tsx");
 const sourceMap=read("src/components/proxy-network-map.tsx");
 assert.match(home,/The interactive 2024 OSM-derived map/);
 assert.match(home,/have <strong>not<\/strong> been matched/);
 assert.match(sourceMap,/not Fingrid-certified substations/);
 assert.match(sourceMap,/ODbL 1.0/);
 assert.match(sourceMap,/onClick/);
});
