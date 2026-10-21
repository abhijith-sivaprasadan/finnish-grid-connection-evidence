import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import archive from "../src/lib/fingrid-archive-coverage-2025.json";
import scenarios from "../src/lib/pypsa-scenario-results.json";
import winter from "../src/lib/pypsa-long-winter-2025.json";

const caseStudy=readFileSync("src/app/case-study/page.tsx","utf8");
const analysis=readFileSync("src/app/analysis/page.tsx","utf8");
const shell=readFileSync("src/components/dashboard-shell.tsx","utf8");

test("Independent workflow page presents four evidence stages and source limits",()=>{
 for(const label of ["Own the grid data","Understand current and future availability",
                    "Screen candidate requests","Model and communicate uncertainty"])
   assert.ok(caseStudy.includes(label), label);
 assert.match(caseStudy,/not a Fingrid product or a connection-approval service/i);
 assert.match(caseStudy,/not operator-calibrated|neither validates|not a historic/i);
 assert.match(caseStudy,/operator-confirmed capacity count of/i);
 assert.match(shell,/href:"\/case-study"/);
});

test("analysis count must be projected from audited source not stale Oct-19 strings",()=>{
 assert.equal(archive.verified_complete_days,171);
 assert.equal(archive.known_missing_source_days,14);
 assert.equal(archive.not_covered_by_archives_days,180);
 assert.match(analysis,/annualArchive\.verified_complete_days/);
 assert.match(analysis,/annualArchive\.known_missing_source_days/);
 assert.match(analysis,/annualArchive\.not_covered_by_archives_days/);
 assert.doesNotMatch(analysis,/150 fully paired UTC days/);
 assert.equal(winter.scenario_count_all_caps,48);
 assert.equal(winter.baseline_count,6);
 assert.match(analysis,/winter\.scenario_count_all_caps/);
 assert.equal(scenarios.scenarios.length,4);
});

test("source-cluster case study distinguishes Grid Scope estimates from model scenarios",()=>{
 assert.match(caseStudy,/not a site|not operator|not a connect|connection-approval/i);
 assert.match(caseStudy,/source review|screenshot|source-record|screenshots/i);
 assert.match(caseStudy,/modelled|model|PyPSA/i);
 assert.match(caseStudy,/\/screening\?demand_mw=100/);
});