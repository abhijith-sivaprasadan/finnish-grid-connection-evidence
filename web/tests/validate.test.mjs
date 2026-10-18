import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const read=(file)=>fs.readFileSync(new URL(file,import.meta.url),"utf8");
test("All API queries use parameter placeholders and no interpolation from URL",()=>{
 for(const route of ["../app/api/v1/capacity/route.ts","../app/api/v1/operations/route.ts"]){
  const src=read(route);
  assert.match(src,/db\(\)\.query/);
  assert.match(src,/\$1/);
  assert.doesNotMatch(src,/NEXT_PUBLIC_DATABASE/);
 }
});
test("Website preserves source disclaimers and real API fetch",()=>{
 const src=read("../app/page.tsx");
 assert.match(src,/independently rechecked|independently validated|independent source-number verification/);
 assert.match(src,/not zero capacity|Missing observations are not zero/);
 assert.match(src,/api\/v1\/capacity/);
 assert.match(src,/api\/v1\/operations/);
 assert.doesNotMatch(src,/DEMO_DATA|mockCapacity/);
});
test("Secret connection only referenced server-side",()=>{
 const src=read("../lib/db.ts");
 assert.match(src,/DATABASE_READ_URL/);
 assert.match(src,/server-only/);
 assert.doesNotMatch(read("../app/page.tsx"),/DATABASE_READ_URL/);
});
