import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import report from "../src/lib/fingrid-archive-coverage-2025.json";

const dates=Array.from({length:365},(_,i)=>new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10));
const inWindow=(day:string,start:string,end:string)=>day>=start&&day<end;
const known=new Set(report.known_missing_original_124_intervals_utc.map(x=>x.slice(0,10)));
const status=dates.map(day=>
  report.original_source_windows.some(w=>inWindow(day,w.start,w.end_exclusive))?"verified":
  known.has(day)?"known_source_gap":"unknown_not_in_archives");

test("original archive bank publishes exactly 171 unique verified source days, not 365",()=>{
 assert.equal(report.status,"verified_original_source_archive_union_partial_2025");
 assert.equal(report.distinct_original_paired_intervals,17640);
 assert.equal(report.verified_complete_days,171);
 assert.equal(report.known_missing_source_days,14);
 assert.equal(report.not_covered_by_archives_days,180);
 assert.equal(report.source_year_complete,false);
 assert.equal(report.annual_pypsa_solved,false);
 assert.equal(report.site_grid_connection_feasible,null);
 assert.deepEqual(report.dataset_ids,[124,74]);
 assert.equal(status.filter(x=>x==="verified").length,171);
 assert.equal(status.filter(x=>x==="known_source_gap").length,14);
 assert.equal(status.filter(x=>x==="unknown_not_in_archives").length,180);
 assert.equal(new Set(report.original_source_windows.map(w=>w.start)).size,12);
 assert.equal(report.original_source_windows.reduce((sum,w)=>sum+w.days,0),171);
 assert.ok(report.original_source_windows.every(w=>w.original_capture_sha256.length===64));
 assert.equal(report.independent_autumn_overlap_original_sha256.length,64);
 assert.match(report.validation_run,/\/actions\/runs\/39452882772$/);
});

test("source gap timeline uses true UTC interval observations, not zeros or site capacity",()=>{
 assert.deepEqual(report.known_missing_original_124_intervals_utc,[
  "2025-01-17T17:00:00Z",
  "2025-01-17T17:45:00Z",
  "2025-02-14T17:00:00Z",
  "2025-02-14T17:45:00Z",
  "2025-03-14T17:00:00Z",
  "2025-03-30T10:45:00Z",
  "2025-04-11T16:15:00Z",
  "2025-04-11T17:15:00Z",
  "2025-04-11T17:45:00Z",
  "2025-04-22T17:00:00Z",
  "2025-05-06T06:45:00Z",
  "2025-05-08T11:30:00Z",
  "2025-05-08T11:45:00Z",
  "2025-05-12T11:30:00Z",
  "2025-05-12T16:15:00Z",
  "2025-05-12T17:45:00Z",
  "2025-05-12T22:00:00Z",
  "2025-05-12T23:45:00Z",
  "2025-05-13T06:45:00Z",
  "2025-05-13T07:00:00Z",
  "2025-05-14T06:15:00Z",
  "2025-05-15T09:15:00Z",
  "2025-05-16T06:30:00Z",
  "2025-05-16T16:15:00Z",
  "2025-07-11T16:15:00Z"
 ]);
 assert.equal(report.authentic_off_grid_quarantined_source_intervals.length,2);
 assert.equal(report.authentic_irregular_native_interval_quarantined_source_intervals.length,1);
 assert.equal(report.authentic_irregular_native_interval_quarantined_source_intervals[0].duration_seconds,1800);
 assert.equal(new Set(report.known_missing_original_124_intervals_utc.map(x=>x.slice(0,10))).size,14);
 assert.equal(status[88],"known_source_gap");
 assert.equal(status[100],"known_source_gap");
 assert.equal(status[111],"known_source_gap");
 assert.equal(status[16],"known_source_gap");
 assert.equal(status[0],"verified");
 assert.equal(status[17],"verified");
 assert.equal(status[196],"unknown_not_in_archives");
 assert.ok(report.boundaries.some(x=>/365 source-complete annual observations|365/i.test(x)));
});

test("coverage page and API are classified as source audit, not 2030 scenario",()=>{
 const page=readFileSync("src/app/analysis/source-coverage/page.tsx","utf8");
 const api=readFileSync("src/app/api/v1/observed/coverage/2025/route.ts","utf8");
 assert.match(page,/source coverage, not grid capability/i);
 assert.match(page,/source_missing|known source/i);
 assert.match(page,/not_in_archives/);
 assert.match(api,/is_calendar_year_source_complete:false/);
 assert.match(api,/is_operational_grid_capacity:false/);
 assert.match(readFileSync("src/app/analysis/page.tsx","utf8"),/\/analysis\/source-coverage/);
 
});
