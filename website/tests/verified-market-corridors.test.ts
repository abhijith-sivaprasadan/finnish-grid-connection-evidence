import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import model from "../src/lib/pypsa-zonal-2025.json";
test("original two real market corridor sources and 24 optimal source-capped models",()=>{
 assert.equal(model.status,"verified_original_source_market_constrained_three_bus_pypsa");
 assert.equal(model.scenario_count,24);
 assert.equal(model.original_source_intervals,2880);
 assert.deepEqual(model.edge_constraints.map(x=>x.fingrid_dataset_id),[38,39]);
 assert.ok(model.edge_constraints.every(x=>x.median_mw>=0&&x.max_mw>=0));
 assert.equal(model.real_operator_substation_connection_capacity,false);
 assert.equal(model.real_line_impedance_and_security_constraints,false);
 assert.equal(model.actual_intraday_access_secured,false);
 assert.equal(model.actual_customer_outages,false);
 assert.equal(model.original_border_csv_sha256.length,64);
 assert.equal(model.original_national_csv_sha256.length,64);
 assert.deepEqual([...new Set(model.scenarios.map(x=>x.corridors_allowed))],["SE1+SE3","SE1_only","SE3_only"]);
 for(const r of model.scenarios){
  const both=model.scenarios.find(s=>s.corridors_allowed==="SE1+SE3"&&s.flex_half_span_mw_assumed===r.flex_half_span_mw_assumed&&s.battery_duration_hours_assumed===r.battery_duration_hours_assumed);
  assert.ok(both);
  if(r.corridors_allowed!=="SE1+SE3")assert.ok(r.modelled_project_relaxation_mwh+1e-3>=both.modelled_project_relaxation_mwh);
 }
 assert.equal(model.scenarios.find(x=>x.corridors_allowed==="SE1_only"&&x.flex_half_span_mw_assumed===50&&x.battery_duration_hours_assumed===8)?.modelled_project_relaxation_mwh,36424.9335);
});
test("physical claim is never implied by website or observed API",()=>{
 const page=readFileSync("src/app/analysis/corridors-2025/page.tsx","utf8");
 const api=readFileSync("src/app/api/v1/model/finland/corridors-2025/route.ts","utf8");
 assert.match(page,/No physical-grid claim/);
 assert.match(page,/not observed|not measured|not operator-measured|never measured/i);
 assert.match(api,/is_physical_ac_dc_power_flow:false/);
 assert.match(api,/operator_confirmed_connection_capacity:false/);
});
