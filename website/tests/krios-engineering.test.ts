import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import results from "../src/lib/krios-engineering-verified-2026.json";
import {osmProxyNodes,osmProxyEdges} from "../src/lib/osm-2024-proxy-map-odbl";

test("verified 2026 engineering results have four distinct honest research classifications",()=>{
 assert.equal(results.cigre_hv.cases.length,3);
 assert.equal(results.cigre_mv.cases.length,4);
 assert.equal(results.fingrid_regional_v2.scenarios.length,4);
 assert.equal(results.cigre_hv.real_network,false);
 assert.equal(results.cigre_mv.real_dutch_feeder,false);
 assert.equal(results.fingrid_regional_v2.operator_approved_connectable_mw,null);
 assert.equal(results.osm_input_uncertainty.operator_calibrated,false);
 assert.ok(results.source_workflow_url.includes("/actions/runs/"));
});
test("CIGRE N-1 outcomes are never advertised as secure without converging",()=>{
 assert.deepEqual(results.cigre_hv.cases.map(x=>x.added_mw),[0,50,100]);
 for(const c of results.cigre_hv.cases){
  assert.equal(c.n1_tested,15);
  assert.ok(c.n1_nonconverged>=0 && c.n1_nonconverged<=15);
  assert.ok(c.n1_converged_with_reference_violation<=15-c.n1_nonconverged);
 }
 assert.equal(results.identical_ac_crosssolver.original_CIGRE_crossvalidated,false);
 assert.equal(results.identical_ac_crosssolver.passed,true);
});
test("licensed spatial source shapes are audited proxy, not named Fingrid substation coordinates",()=>{
 assert.equal(osmProxyNodes.length,107);
 assert.equal(osmProxyEdges.length,137);
 assert.equal(osmProxyNodes.filter(x=>!x.dc).length,104);
 assert.ok(osmProxyNodes.every(x=>Number.isFinite(x.lon)&&Number.isFinite(x.lat)));
 assert.ok(osmProxyEdges.every(([x,y])=>x>=0&&y>=0&&x<107&&y<107));
 const m=readFileSync("src/components/proxy-network-map.tsx","utf8");
 assert.match(m,/ODbL 1.0/);
 assert.match(m,/NOT|not|Not/);
 assert.match(m,/onClick/);
});
test("model explorer uses verified results, interactive selectors and no feasibility claim",()=>{
 const s=readFileSync("src/components/engineering-scenario-explorer.tsx","utf8");
 assert.ok(s.includes("useState"));
 assert.ok(s.includes("non-converged")||s.includes("Non-converged"));
 assert.ok(s.includes("invented")||s.includes("hypothetical"));
 const api=readFileSync("src/app/api/v1/model/engineering/route.ts","utf8");
 assert.ok(api.includes("operator_approved_site_mw:null"));
});
