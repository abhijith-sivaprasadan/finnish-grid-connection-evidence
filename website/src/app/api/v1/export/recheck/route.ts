import { capacities } from "@/lib/repository";
import { auditWorksheet } from "@/lib/workbench";

export const dynamic="force-dynamic";
export async function GET() {
  try {
    const result=await capacities(new URLSearchParams("limit=200"));
    return new Response(auditWorksheet(result.data),{headers:{
      "Content-Type":"text/csv; charset=utf-8",
      "Content-Disposition":'attachment; filename="fingrid-grid-scope-independent-recheck.csv"',
      "Cache-Control":"no-store",
      "X-Content-Type-Options":"nosniff",
    }});
  } catch {
    return Response.json({error:{code:"SOURCE_UNAVAILABLE",message:"Evidence store temporarily unavailable."}},
      {status:503,headers:{"cache-control":"no-store"}});
  }
}
