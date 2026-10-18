import {db,publicError,responseHeaders} from "@/lib/db";
export const runtime="nodejs";
export async function GET() {
  try {
    const rows=await db().query("SELECT connection_point_id, name, operator, voltage_kv, source_url FROM connection_point ORDER BY name LIMIT 100");
    return Response.json({data:rows.rows,meta:{count:rows.rowCount,scope:"selected source-transcribed connection points"}},{headers:responseHeaders});
  } catch {return publicError();}
}
