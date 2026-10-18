import test from "node:test";
import assert from "node:assert/strict";
// @ts-expect-error Node ESM script is intentionally plain JavaScript; tested at runtime with tsx.
import { evaluateEvidence } from "../scripts/check-public-site.mjs";

const snapshot = { points:5, capacity_observations:18, operational_rows_stored:0,
  newest_operational_interval_utc:null, source_values_independently_verified:false, data_mode:"compiled_snapshot" };
const live = { ...snapshot, data_mode:"neon", operational_rows_stored:288,
  newest_operational_interval_utc:"2026-10-16T00:00:00.000Z" };

test("monitor allows transparently declared snapshot but not imaginary healthy database",()=>{
  assert.equal(evaluateEvidence(snapshot).mode,"compiled_snapshot");
  assert.throws(()=>evaluateEvidence(snapshot,{requireLive:true}),/Expected Neon/);
});
test("live-mode monitor accepts real, recent UTC evidence and rejects stale records",()=>{
  assert.equal(evaluateEvidence(live,{requireLive:true,now:Date.parse("2026-10-18T00:00:00.000Z")}).mode,"neon");
  assert.throws(()=>evaluateEvidence(live,{requireLive:true,now:Date.parse("2026-11-01T00:00:00.000Z")}),/stale/);
});
test("monitor fails if the source is falsely declared independently verified",()=>{
  assert.throws(()=>evaluateEvidence({...snapshot,source_values_independently_verified:true}),/verified/);
  assert.throws(()=>evaluateEvidence({...snapshot,points:0}),/connection points/);
});
