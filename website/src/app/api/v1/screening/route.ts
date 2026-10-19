import { evidenceCatalogue } from "@/lib/catalogue";
import { handleApi } from "@/lib/http";
import { parseScreening, screenRecords } from "@/lib/screening";
export const runtime="nodejs";
export const dynamic="force-dynamic";
export async function GET(request:Request){
 return handleApi(async()=>{
  const criteria=parseScreening(new URL(request.url).searchParams);
  const source=await evidenceCatalogue();
  return screenRecords(source.stations,source.observations,criteria);
 });
}
