import { readQuery } from "@/lib/db";
import { response } from "@/lib/http";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export async function GET() {
  try {
    await readQuery("SELECT 1 AS ready");
    return response({status:"ok",store:"connected",writes_enabled:false});
  } catch {
    return response({status:"degraded",store:"unavailable",writes_enabled:false},503);
  }
}
