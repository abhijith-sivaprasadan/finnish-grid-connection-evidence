import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import study from "../src/lib/pypsa-verified-seasonal-2025.json";

test("only the source-verified 14-day matched 2025 seasonal model runs may be published",()=>{
 assert.equal(study.study_status,"verified_14_day_per_season_source_and_solver");
 assert.equal(study.data_kind,"model_scenario");
 assert.equal(study.annual_2025_verified_complete,false);
 assert.equal(study.model_feasibility_claim,false);
 assert.equal(study.modelled_days_per_season,14);
 assert.equal(study.source_pairs_per_season,1344);
 assert.equal(study.assumptions.new_demand_energy_mwh_per_season,33600);
 assert.deepEqual(study.source_urls.map(x=>x.split("/").pop()),["124","74"]);
 assert.deepEqual(study.model_windows.map(x=>x.season),["winter","summer","autumn"]);
 assert.deepEqual(study.model_windows.map(x=>x.start_utc.slice(0,10)),["2025-01-18","2025-06-15","2025-09-15"]);
 assert.deepEqual(study.model_windows.map(x=>x.end_utc.slice(0,10)),["2025-02-01","2025-06-29","2025-09-29"]);
 assert.ok(study.model_windows.every(x=>x.sha256.length===64));
 assert.deepEqual(["winter","summer","autumn"].map(x=>study.original_30day_audit[x as "winter"|"summer"|"autumn"].complete_days),[29,29,30]);
 assert.equal(study.original_30day_audit.winter.missing_utc.length,2);
 assert.equal(study.original_30day_audit.summer.missing_utc.length,1);
 assert.equal(study.original_30day_audit.autumn.missing_utc.length,0);
 assert.equal(study.source_artifact_id,12251493864);
 assert.match(study.source_validation_run,/\/actions\/runs\/39396079522/);
});
test("all twelve sensitivity values are preserved including legitimate negative increments",()=>{
 assert.equal(study.scenario_results.length,12);
 const get=(cap:number,flex:number,batt:number)=>
  study.scenario_results.find(x=>x.balancing_limit_mw===cap&&x.flex_half_span_mw===flex&&x.battery_power_mw===batt)!;
 assert.ok(study.scenario_results.every(r=>
  ["winter","summer","autumn"].every(season=>Number.isFinite(r.incremental_penalty_shortfall_mwh[season as "winter"|"summer"|"autumn"]))));
 assert.deepEqual(get(1500,0,0).incremental_penalty_shortfall_mwh,{winter:4841.335,summer:2091.805,autumn:4622.33});
 assert.deepEqual(get(1500,50,100).incremental_penalty_shortfall_mwh,{winter:1620.6092,summer:-132.9899,autumn:1708.7306});
 assert.equal(get(2000,50,100).incremental_penalty_shortfall_mwh.winter,-51.6225);
 assert.deepEqual([...new Set(study.scenario_results.map(x=>x.balancing_limit_mw))],[1000,1500,2000]);
});
test("site page, source audit, API preserve nonannual and nonfeasibility qualifiers",()=>{
 const page=readFileSync("src/app/analysis/seasons/page.tsx","utf8");
 const client=readFileSync("src/components/verified-seasonal-comparison.tsx","utf8");
 const api=readFileSync("src/app/api/v1/model/finland/seasons/route.ts","utf8");
 assert.match(page,/not.*complete|full-year.*rejected/i);
 assert.match(page,/source_validation_run/);
 assert.match(client,/annual_2025_verified_complete|source.complete|original_30day_audit/i);
 assert.match(client,/incremental_penalty_shortfall_mwh/);
 assert.match(client,/negative|Negative/i);
 assert.match(api,/is_operator_confirmed_capacity:false/);
 assert.match(readFileSync("src/app/analysis/page.tsx","utf8"),/\/analysis\/seasons/);
});
