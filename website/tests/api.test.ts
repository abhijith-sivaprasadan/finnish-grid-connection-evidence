import test from "node:test";
import assert from "node:assert/strict";
import { BadInput, operationsParams, pageParams, directionParam, pointParam } from "../src/lib/params";
import { capacities, coverage, operations, points } from "../src/lib/repository";
import { handleApi } from "../src/lib/http";

test("query bounds reject malformed pagination and unrecognized directions", () => {
  assert.throws(()=>pageParams(new URLSearchParams("limit=10000")), BadInput);
  assert.throws(()=>pageParams(new URLSearchParams("offset=-1")), BadInput);
  assert.throws(()=>directionParam(new URLSearchParams("direction=made-up")), BadInput);
  assert.throws(()=>pointParam(new URLSearchParams("point_id=abc';DROP TABLE")), BadInput);
});
test("operations reject mismatched dataset, ambiguous timezones, and large windows",()=>{
  const now=new Date("2026-10-18T00:00:00Z");
  assert.throws(()=>operationsParams(new URLSearchParams("source=fingrid&dataset_id=A65"),now),BadInput);
  assert.throws(()=>operationsParams(new URLSearchParams("from=2026-10-15T00:00:00"),now),BadInput);
  assert.throws(()=>operationsParams(new URLSearchParams("from=2026-01-01T00:00:00Z"),now),BadInput);
  const result=operationsParams(new URLSearchParams("source=entsoe&dataset_id=A65"),now);
  assert.equal(result.from,"2026-10-04T00:00:00.000000Z");
  assert.equal(result.to,"2026-10-18T00:00:00.000000Z");
});
test("capacity filters are parameterized, never interpolated SQL",async()=>{
  const calls:{sql:string;values:unknown[]}[]=[];
  const query=async <T extends Record<string,unknown>>(sql:string,values:unknown[]=[]):Promise<T[]>=>{
    calls.push({sql,values});return sql.includes("count(*)")?[{total:0}] as unknown as T[]:[];
  };
  const p=new URLSearchParams({point_id:"FI-FINGRID-ALAPITKA-400",direction:"production",year:"2030",limit:"5"});
  const output=await capacities(p,query);
  assert.equal(output.data.length,0);
  assert.equal(output.pagination.total,0);
  assert.equal(calls.length,2);
  assert.deepEqual(calls[0].values,["production",2030,"FI-FINGRID-ALAPITKA-400"]);
  assert.ok(calls[0].sql.includes("direction = $1"));
  assert.ok(calls[0].sql.includes("effective_year = $2"));
  assert.ok(calls[0].sql.includes("connection_point_id = $3"));
  assert.ok(!calls[1].sql.includes("FI-FINGRID-ALAPITKA-400"));
  assert.match(output.limitations[0],/not independently rechecked/);
});
test("operations preserve 31-day bounded source scope and most recent revision view",async()=>{
  const calls:string[]=[];
  const query=async <T extends Record<string,unknown>>(sql:string):Promise<T[]>=>{
    calls.push(sql);return sql.includes("count(*)")?[{total:0}] as unknown as T[]:[];
  };
  const r=await operations(new URLSearchParams("source=fingrid&dataset_id=124"),query,new Date("2026-10-18T00:00:00Z"));
  assert.equal(r.pagination.total,0);
  assert.ok(calls[0].includes("latest_operational"));
  assert.ok(calls[1].includes("timestamp_utc DESC"));
  assert.match(r.limitations[0],/not substation telemetry/);
});
test("coverage accurately distinguishes recorded vs absent intersections",async()=>{
  const base={operator:"Fingrid",voltage_kv:400,source_url:"https://operator.example"};
  const pts=[{connection_point_id:"FI-FINGRID-ALAPITKA-400",name:"ALAPITKÄ 400 kV",...base}];
  const obs=[{connection_point_id:pts[0].connection_point_id,direction:"production",effective_year:2030,
    capacity_value:380,capacity_unit:"MW",source_observed_at:"2026-10-17T18:00:00Z"}];
  const query=async <T extends Record<string,unknown>>(sql:string):Promise<T[]> =>
    sql.includes("FROM connection_point")?pts as unknown as T[]:obs as unknown as T[];
  const result=await coverage(new URLSearchParams(),query);
  assert.equal(result.coverage.intersections,6);
  assert.equal(result.coverage.published,1);
  assert.equal(result.coverage.missing_in_compiled_capture,5);
  assert.equal(result.data.find(x=>x.year===2030&&x.direction==="production")?.value,380);
  assert.equal(result.data.find(x=>x.year===2030&&x.direction==="consumption")?.value,null);
});
test("API converts invalid input to 400 and DB failure to nonrevealing 503",async()=>{
  const bad=await handleApi(async()=>{throw new BadInput("limit")});
  assert.equal(bad.status,400);assert.equal((await bad.json()).error.code,"INVALID_QUERY");
  const leaked="postgresql://private:secret@domain/database";
  const unavailable=await handleApi(async()=>{throw new Error(leaked)});
  assert.equal(unavailable.status,503);
  assert.ok(!(await unavailable.text()).includes(leaked));
});
test("point list uses hard pagination limits even without data",async()=>{
  const query=async <T extends Record<string,unknown>>(sql:string):Promise<T[]> =>
    sql.includes("count(*)")?[{total:0}] as unknown as T[]:[];
  const r=await points(new URLSearchParams("limit=100"),query);
  assert.equal(r.pagination.limit,100);
  await assert.rejects(()=>points(new URLSearchParams("limit=101"),query),BadInput);
});
