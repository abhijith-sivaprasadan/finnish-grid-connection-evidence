import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import data from "../src/lib/netherlands-official-source-summary-2026.json";
import {parseScreening,screenRecords} from "../src/lib/screening";
import {snapshotPoints,snapshotCapacities} from "../src/lib/snapshot";

test("three original Netherlands CSVs have verified distinct native hashes and no Dutch site headroom",()=>{
 assert.equal(data.source_country,"NL");
 assert.equal(data.original_csvs.length,3);
 assert.equal(data.original_csvs.reduce((s,v)=>s+v.row_count,0),896);
 assert.deepEqual(data.original_csvs.map(x=>x.row_count),[23,271,602]);
 assert.equal(new Set(data.original_csvs.map(x=>x.sha256)).size,3);
 assert.ok(data.original_csvs.every(x=>/^[0-9a-f]{64}$/.test(x.sha256)));
 assert.equal(data.site_specific_available_mw,null);
 assert.equal(data.license_for_raw_derivative_redistribution_verified,false);
 assert.equal(data.raw_rows_published,false);
});
test("Netherlands historical categorical values are not interpreted as connection availability",()=>{
 const r=data.original_csvs[1];
 assert.ok("original_label_counts" in r);
 const codes=r.original_label_counts;
 if(!codes)throw new Error("Official code counts missing");
 assert.deepEqual(codes.afname,{"0":11,"1":70,"3":190});
 assert.deepEqual(codes.opwek,{"0":67,"1":6,"3":198});
 assert.equal(Object.values(codes.afname).reduce((a,b)=>a+b,0),r.row_count);
 assert.equal(Object.values(codes.opwek).reduce((a,b)=>a+b,0),r.row_count);
 const page=readFileSync("src/app/netherlands/page.tsx","utf8");
 assert.match(page,/not inferred|not a live site|without fabricated capacity|NOT/i);
 assert.match(page,/unmapped|untranslated|original categorical/i);
 assert.ok(page.includes("/api/v1/netherlands/source-summary"));
});
test("Fingrid source-readiness never changes original two indicative matches or operator security claims",()=>{
 const input=parseScreening(new URLSearchParams("demand_mw=100&year=2030&connection_type=switchyard"));
 const r=screenRecords(snapshotPoints,snapshotCapacities,input);
 assert.equal(r.summary.indicative_threshold_met,2);
 assert.equal(r.summary.unknown_not_captured,3);
 assert.equal(r.summary.operator_confirmed_feasible,0);
 assert.equal(r.results.filter(x=>x.connection_pathway==="review_lower_voltage_switchyard").length,5);
 assert.equal(r.results.filter(x=>x.evidence_status==="indicative_threshold_met"&&x.connection_pathway==="review_lower_voltage_switchyard").length,2);
 assert.ok(r.results.every(x=>x.next_actions.length>0&&x.verified_reinforcement_for_this_point===false));
});
test("downloadable human-readable engineering brief is implemented as evidence not permit",()=>{
 const s=readFileSync("src/components/screening-workbench.tsx","utf8");
 assert.match(s,/downloadBrief/);
 assert.match(s,/Source link: /);
 assert.match(s,/Operator-approved connection: No claim/);
 assert.match(s,/connection_type/);
 assert.match(s,/Requested.*MW|requested:.*MW/i);
});
