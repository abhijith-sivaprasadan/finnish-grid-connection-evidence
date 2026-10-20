import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import winter from "../src/lib/pypsa-long-winter-2025.json";
import borders from "../src/lib/pypsa-border-observed-2025.json";
test("27-day original source studies solve with assumptions but no confirmed local grid capacity",()=>{
 assert.equal(winter.source_run,39419524961);
 assert.equal(winter.scenario_count_all_caps,48);
 assert.equal(winter.baseline_count,6);
 assert.equal(winter.complete_2025_year,false);
 assert.equal(winter.verified_operator_connection_capacity,false);
 assert.deepEqual(winter.model_windows.map(w=>w.days),[27,27]);
 assert.ok(winter.model_windows.every(w=>w.source_sha256.length===64&&w.scenarios.length===8));
 assert.equal(winter.model_windows[0].scenarios[7].incremental_model_penalty_slack_mwh,2811.1534);
 assert.equal(winter.model_windows[1].scenarios[7].incremental_model_penalty_slack_mwh,17783.6722);
});
test("Fingrid Swedish-border sources preserve commercial sign and intraday, not physical capacity, semantics",()=>{
 assert.equal(borders.source_run,39420079414);
 assert.equal(borders.complete_days,30);
 assert.equal(borders.observed_quarter_hour_count,2880);
 assert.deepEqual(Object.keys(borders.source_sha256_by_dataset),["31","32","38","39"]);
 assert.ok(Object.values(borders.source_sha256_by_dataset).every(x=>x.length===64));
 assert.ok(borders.observed_statistics.fi_se1_commercial_signed_mean_mw<0);
 assert.ok(borders.observed_statistics.fi_se3_commercial_signed_mean_mw<0);
 assert.equal(borders.observed_statistics.unused_intraday_import_SE1_SE3_median_mw,553.6);
 assert.equal(borders.scenarios.length,8);
 assert.ok(borders.limitations.some(x=>/not total physical/i.test(x)));
});
test("research and API preserve model classification and no operator-confirmed capacity",()=>{
 const page=readFileSync("src/app/analysis/borders-2025/page.tsx","utf8");
 assert.match(page,/Not a 2030 grid-connection study/);
 assert.match(page,/not observed unmet load/i);
 assert.match(readFileSync("src/app/api/v1/model/finland/winter-2025/route.ts","utf8"),/operator_confirmed_capacity:false/);
 assert.match(readFileSync("src/app/api/v1/model/finland/borders-2025/route.ts","utf8"),/guaranteed_import_rights:false/);
});
