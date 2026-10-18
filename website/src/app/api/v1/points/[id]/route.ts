import { point } from "@/lib/repository";
import { handleApi,response } from "@/lib/http";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export async function GET(_request:Request,ctx:{params:Promise<{id:string}>}) {
  return handleApi(async()=>{
    const {id}=await ctx.params;
    const found=await point(id);
    if(!found) return {error:{code:"NOT_FOUND",message:"Connection point not in compiled sample."}};
    return {data:found,limitations:["Indicative source only; not confirmed connection headroom."]};
  }).then(async res=>{
    const data=await res.clone().json();
    return data?.error?.code==="NOT_FOUND"?response(data,404):res;
  });
}
