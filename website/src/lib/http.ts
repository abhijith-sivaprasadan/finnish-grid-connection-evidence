import { BadInput } from "./params";

export function response(data: unknown, status=200) {
  return Response.json(data,{status,headers:{
    "Cache-Control":status===200?"public, s-maxage=120, stale-while-revalidate=300":"no-store",
    "X-Content-Type-Options":"nosniff",
  }});
}
export async function handleApi<T>(fn:()=>Promise<T>) {
  try { return response(await fn()); }
  catch(error) {
    if (error instanceof BadInput) return response({error:{code:"INVALID_QUERY",message:error.message}},400);
    // Never return SQL messages, network exceptions, schema info or secrets.
    return response({error:{code:"SOURCE_UNAVAILABLE",message:"Read-only evidence store temporarily unavailable."}},503);
  }
}
