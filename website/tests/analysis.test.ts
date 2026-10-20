import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import model from "../src/lib/pypsa-scenario-results.json";
import observed from "../src/lib/finland-observed.json";
const read=(path:string)=>readFileSync(path,"utf8");
test("model study publishes four optimal audited sensitivities, never grid feasibility",()=>{
 assert.equal(model.publication_status,"verified_solver_output");
 assert.equal(model.model_version,"pypsa-fi-single-bus-v1");
 assert.equal(model.classification,"model_scenario");
 assert.equal(model.verified_operator_connectability,false);
 assert.match(model.model_resolution,/aggregate Finland bus/i);
 assert.equal(model.scenarios.length,4);
 assert.deepEqual(model.scenarios.map(s=>s.scenario),[
 "observed_reference","flat_100mw","flexible_100mw","flat_100mw_with_battery"
 ]);
 assert.ok(model.scenarios.every(s=>s.solver_status==="ok"&&s.termination==="optimal"));
 assert.ok(model.scenarios.every(s=>s.max_model_balance_error_mw<1e-5));
 assert.deepEqual(model.scenarios.map(s=>s.new_demand_mwh),[0,4800,4800,4800]);
 assert.deepEqual(model.scenarios.map(s=>s.modelled_shortfall_under_assumption_mwh),
  [1267.3275,1642.3275,1454.8275,1267.3275]);
 assert.equal(model.assumptions.balancing_support_limit_mw,1500);
 assert.equal(model.assumptions.balancing_cost_proxy.includes("not a market price"),true);
 assert.equal(model.source_urls.length,2);
 assert.equal(model.observed_input_sha256.length,64);
 assert.match(model.source_job_url,/actions\/runs\/\d+\/job\/\d+/);
});
test("source-paired historical 15-min observations are real, attributed and separate",()=>{
 const rows=observed.time_series;
 assert.equal(rows.length,192);
 assert.equal(rows[0].timestamp_utc.slice(0,10),"2026-10-15");
 assert.equal(rows[191].timestamp_utc.slice(0,10),"2026-10-16");
 assert.equal(observed.data_kind,"observed_fingrid_national_aggregate");
 assert.equal(observed.source_unit,"MWh/h (interval-average MW)");
 assert.deepEqual(observed.source_datasets.map(d=>d.id),["124","74"]);
 assert.ok(rows.every(r=>Number.isFinite(r.consumption_mw)&&Number.isFinite(r.production_mw)));
 assert.ok(rows.every(r=>r.consumption_retrieved_at&&r.production_retrieved_at));
 for(let i=1;i<rows.length;i++)
  assert.equal(Date.parse(rows[i].timestamp_utc)-Date.parse(rows[i-1].timestamp_utc),15*60000);
});
test("analysis page and read-only model API forbid station headroom claims",()=>{
 const page=read("src/app/analysis/page.tsx");
 const component=read("src/components/analysis-workbench.tsx");
 const api=read("src/app/api/v1/model/finland/route.ts");
 const shell=read("src/components/dashboard-shell.tsx");
 const home=read("src/app/page.tsx");
 assert.match(page,/not.*2030 forecast/i);
 assert.match(page,/not.*grid/i);
 assert.match(page,/Fingrid Open Data|Fingrid/);
 assert.match(component,/not actual outages|not an observed Finnish blackout|not actual outages/i);
 assert.match(component,/source_job_url/);
 assert.match(component,/modelled_shortfall_under_assumption_mwh/);
 assert.match(component,/Export solved scenario CSV/);
 assert.match(api,/is_operator_confirmed_capacity:false/);
 assert.match(shell,/\/analysis/);
 assert.match(home,/\/analysis/);
});
