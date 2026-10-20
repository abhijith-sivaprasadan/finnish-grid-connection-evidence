import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import study from "../src/lib/pypsa-extended-sensitivity.json";

test("published 30-day 2025 national source summary comes from completed run, not fabricated point MW",()=>{
 assert.equal(study.publication_state,"completed_source_and_solver_verified");
 assert.equal(study.data_kind,"model_scenario");
 assert.equal(study.source_kind,"observed_national_Fingrid_2025");
 assert.equal(study.complete_days,30);
 assert.equal(study.source_intervals,2880);
 assert.equal(study.input_start_utc,"2025-09-15T00:00:00Z");
 assert.equal(study.input_end_utc,"2025-10-15T00:00:00Z");
 assert.equal(study.source_csv_sha256,"3093f704484848919d83feb6c133c2e2abf2299566d5bd02a109e01b7fdec2e0");
 assert.equal(study.operator_confirmed_grid_capacity,false);
 assert.equal(study.national_shortfall_observed,false);
 assert.equal(study.forecast_year,null);
 assert.deepEqual(study.model_assumptions.balancing_ceiling_mw,[1000,1500,2000]);
 assert.equal(study.results.length,12);
 assert.equal(study.source_run.workflow_run_id,39391985966);
 assert.match(study.source_run.job_url,/github.com\/.*\/actions\/runs\/.*\/job\//);
 assert.equal(new Set(study.results.map(r=>[r.balancing_limit_mw_assumed,r.flex_half_range_mw_assumed,r.battery_power_mw_assumed].join("|"))).size,12);
 assert.ok(study.results.every(r=>r.added_load_energy_mwh===72000&&r.solver_status==="ok"&&r.solver_termination==="optimal"&&r.max_balance_error_mw<1e-5));
 assert.ok(study.results.every(r=>Math.abs(r.shortfall_mwh_under_assumed_limit-r.baseline_shortfall_mwh_under_same_assumed_limit-r.incremental_shortfall_vs_reference_mwh)<0.001));
});
test("new published read-only API and visualization preserve scope caveats",()=>{
 const page=readFileSync("src/app/analysis/sensitivity/page.tsx","utf8");
 const viewer=readFileSync("src/components/extended-sensitivity.tsx","utf8");
 const api=readFileSync("src/app/api/v1/model/finland/sensitivity/route.ts","utf8");
 assert.match(page,/Not real shortages or connection headroom/);
 assert.match(page,/data.source_run.workflow_url/);
 assert.match(page,/SHA-256/);
 assert.match(viewer,/incremental_shortfall_vs_reference_mwh/);
 assert.match(viewer,/hypothetical|Hypothetical/);
 assert.match(api,/is_operator_confirmed_capacity:false/);
 assert.match(readFileSync("src/app/analysis/page.tsx","utf8"),/\/analysis\/sensitivity/);
});
