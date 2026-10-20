import test from "node:test";
import assert from "node:assert/strict";
import { snapshotCapacities } from "../src/lib/snapshot";
import { sourceReviewStatus, EXACT_TOOLTIP_COUNT, PANEL_VALUE_COUNT, REVIEWED_SAMPLE_SIZE } from "../src/lib/verification";
import audit from "../src/lib/grid-scope-audit.json";

test("18 original snapshot observations have exactly bound screenshot matches",()=>{
 assert.equal(REVIEWED_SAMPLE_SIZE,18);
 assert.equal(EXACT_TOOLTIP_COUNT,17);
 assert.equal(PANEL_VALUE_COUNT,1);
 assert.equal(snapshotCapacities.length,18);
 assert.deepEqual(new Set(audit.map(r=>r.observation_id)).size,18);
 for(const r of snapshotCapacities) {
   const status=sourceReviewStatus(r);
   assert.equal(status.status,"screenshot_match",r.observation_id);
   assert.ok(status.grade==="exact_tooltip"||status.grade==="explicit_panel_number");
 }
});
test("screenshots do not grant audit status to changed values or new captures",()=>{
 const base=snapshotCapacities[0];
 for(const change of [
  {capacity_value:base.capacity_value+1},
  {capacity_unit:"MVA"},
  {effective_year:2027},
  {direction:"consumption"},
  {connection_point_id:"FI-FINGRID-UNKNOWN-400"},
  {observation_id:"new-2026-observation"},
  {source_observed_at:"2026-10-19T18:46:43Z"},
  {source_url:"https://example.com/different-capture"},
 ]) {
  assert.equal(sourceReviewStatus({...base,...change}).status,"not_audited",JSON.stringify(change));
 }
});
test("PostgreSQL fractional UTC timestamp formatting does not invalidate original review",()=>{
 const base=snapshotCapacities[0];
 assert.equal(sourceReviewStatus({...base,source_observed_at:"2026-10-17T18:46:43.000000Z"}).status,"screenshot_match");
 assert.equal(sourceReviewStatus({...base,source_observed_at:"invalid timestamp"}).status,"not_audited");
 // Date.parse() rounds/truncates to milliseconds. These genuinely different
 // UTC instants MUST not inherit the original screenshot-review evidence.
 assert.equal(sourceReviewStatus({...base,source_observed_at:"2026-10-17T18:46:43.000001Z"}).status,"not_audited");
 assert.equal(sourceReviewStatus({...base,source_observed_at:"2026-10-17T18:46:43.000999Z"}).status,"not_audited");
 assert.equal(sourceReviewStatus({...base,source_observed_at:"2026-10-17T18:46:43.000000+00:00"}).status,"not_audited");
});
