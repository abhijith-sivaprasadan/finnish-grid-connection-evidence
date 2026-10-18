import test from "node:test";
import assert from "node:assert/strict";
import { assessQuality, auditRecords, auditWorksheet, boundsFromLatest, chooseDays, csvTable, operationalWindow } from "../src/lib/workbench";
import { snapshotCapacities } from "../src/lib/snapshot";

test("audit covers every original transcription and cannot silently certify it",()=>{
  const records=auditRecords(snapshotCapacities);
  assert.equal(records.length,18);
  assert.ok(records.every(r=>r.independent_recheck_status==="pending_independent_recheck"));
  assert.equal(new Set(records.map(r=>r.observation_id)).size,18);
  const csv=auditWorksheet(snapshotCapacities);
  assert.equal(csv.trimEnd().split("\r\n").length,19);
  assert.match(csv,/reviewed_at_utc,reviewer,current_value,current_unit/);
  assert.doesNotMatch(csv,/matches_transcription|operator_confirmed/);
});
test("audit CSV safely quotes source notes with commas and quotes",()=>{
 const c=csvTable(["name","note"],[{name:"A",note:'"quoted", line'}]);
 assert.match(c,/'?A,"""quoted"", line"/);
});
test("UTC windows end after the latest completed day with no silent 500-row truncation",async()=>{
 const b=boundsFromLatest("2026-10-17T00:00:00.000000Z",3);
 assert.equal(b.from,"2026-10-14T00:00:00.000000Z");
 assert.equal(b.to,"2026-10-17T00:00:00.000000Z");
 assert.equal(chooseDays("7"),7);
 assert.throws(()=>chooseDays("14"));
 const seen:{sql:string,args:unknown[]}[]=[];
 const q=async<T extends Record<string,unknown>>(sql:string,args:unknown[]=[]):Promise<T[]>=>{
   seen.push({sql,args});return [] as T[];
 };
 const r=await operationalWindow("2026-10-17T00:00:00Z",7,q);
 assert.equal(r.data.length,0);
 assert.equal(seen.length,1);
 assert.ok(seen[0].sql.includes("latest_operational"));
 assert.ok(seen[0].sql.includes("LIMIT 2100"));
 assert.ok(!seen[0].sql.includes("UNION ALL"));
});
test("quality evaluates interval coverage, discontinuities and revisions without conflation",()=>{
 const sample=[{source:"fingrid",dataset_id:"124",day_utc:"2026-10-16",intervals:"96",
  stored_rows:"100",gaps:"0",first_start:"2026-10-16T00:00:00Z",last_end:"2026-10-17T00:00:00Z",
  latest_retrieved:"2026-10-18T11:00:00Z"}];
 const valid=assessQuality(sample);
 assert.equal(valid[0].complete,true);
 assert.equal(valid[0].revisions,4);
 assert.equal(assessQuality([{...sample[0],gaps:"1"}])[0].complete,false);
 assert.equal(assessQuality([{...sample[0],intervals:"95"}])[0].complete,false);
 assert.equal(assessQuality([{...sample[0],first_start:"2026-10-16T00:15:00Z"}])[0].complete,false);
});
