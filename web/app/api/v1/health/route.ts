import { db } from "@/lib/db";
export const runtime = "nodejs";
export async function GET() {
  try { await db().query("SELECT 1");
    return Response.json({status:"ok",service:"finnish-grid-evidence",database:"reachable",version:"v1"},{headers:{"Cache-Control":"no-store"}});
  } catch { return Response.json({status:"degraded",service:"finnish-grid-evidence",database:"unreachable",version:"v1"},{status:503,headers:{"Cache-Control":"no-store"}}); }
}
