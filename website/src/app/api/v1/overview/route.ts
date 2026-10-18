import { overview } from "@/lib/repository";
import { handleApi } from "@/lib/http";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export async function GET() {return handleApi(()=>overview());}
