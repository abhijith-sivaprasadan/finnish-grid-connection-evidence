import {db,publicError,responseHeaders} from "@/lib/db";
import {boundedInt,choice} from "@/lib/validate";
export const runtime="nodejs";
export async function GET(request:Request) {
  const params=new URL(request.url).searchParams;
  const source=params.get("source");
  if(source && !choice(source,["fingrid","entsoe"])) return Response.json({error:{code:"INVALID_SOURCE"}},{status:400});
  const limit=boundedInt(params.get("limit"),750,2000);
  if(limit===null) return Response.json({error:{code:"INVALID_LIMIT"}},{status:400});
  try {
    const result=await db().query(`SELECT source,dataset_id,metric,unit,value,
      timestamp_utc,interval_end_utc,retrieved_at,source_url,area
      FROM latest_operational WHERE ($1::text IS NULL OR source=$1)
      ORDER BY timestamp_utc DESC LIMIT $2`,[source,limit]);
    return Response.json({data:result.rows,meta:{count:result.rowCount,scope:"Finland-wide operational context only; not node connection capacity",time_zone:"UTC",latest_record_end_utc:result.rows.reduce((a,r)=>a>r.interval_end_utc?a:r.interval_end_utc,"")}},{headers:responseHeaders});
  }catch{return publicError();}
}
