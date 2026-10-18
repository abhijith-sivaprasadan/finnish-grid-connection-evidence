import { coverage } from "@/lib/repository";
import { handleApi } from "@/lib/http";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export async function GET(request:Request) {
  return handleApi(()=>coverage(new URL(request.url).searchParams));
}
