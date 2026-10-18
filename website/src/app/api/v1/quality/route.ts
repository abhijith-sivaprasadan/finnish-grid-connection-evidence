import { overview } from "@/lib/repository";
import { qualityReport } from "@/lib/workbench";
import { handleApi } from "@/lib/http";
export const dynamic="force-dynamic";
export async function GET() {
  return handleApi(async()=>{
    const state=await overview();
    if(state.data_mode==="compiled_snapshot"||!state.newest_operational_interval_utc)
      return {data_mode:state.data_mode,rows:[],sources:[],disclaimer:"No operational database intervals available."};
    const report=await qualityReport(state.newest_operational_interval_utc);
    return {...report,data_mode:"neon"};
  });
}
