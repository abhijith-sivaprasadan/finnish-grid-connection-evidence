import {db,publicError,responseHeaders} from "@/lib/db";
import {choice,year} from "@/lib/validate";
export const runtime="nodejs";
export async function GET(request:Request) {
  const params=new URL(request.url).searchParams;
  const direction=params.get("direction");
  if(direction && !choice(direction,["consumption","production"])) return Response.json({error:{code:"INVALID_DIRECTION"}},{status:400});
  const y=year(params.get("year"));
  if(Number.isNaN(y)) return Response.json({error:{code:"INVALID_YEAR"}},{status:400});
  const point=params.get("point");
  if(point && !/^FI-FINGRID-[A-Z0-9-]{1,64}$/.test(point)) return Response.json({error:{code:"INVALID_POINT"}},{status:400});
  try{
    const sql=`SELECT observation_id,connection_point_id,name,direction,effective_year,
      capacity_value,capacity_unit,capacity_status,source_url,source_observed_at,
      source_published_on,validity_notes
      FROM published_capacity
      WHERE ($1::text IS NULL OR direction=$1)
        AND ($2::integer IS NULL OR effective_year=$2)
        AND ($3::text IS NULL OR connection_point_id=$3)
      ORDER BY name,direction,effective_year,source_observed_at DESC LIMIT 500`;
    const result=await db().query(sql,[direction,y,point]);
    return Response.json({data:result.rows,meta:{count:result.rowCount,kind:"published_indicative",independently_verified:false,note:"These are source transcriptions, not guaranteed connectable capacity. Missing values are unknown, not zero."}},{headers:responseHeaders});
  }catch{return publicError();}
}
