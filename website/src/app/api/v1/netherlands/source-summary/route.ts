import audit from "@/lib/netherlands-official-source-summary-2026.json";
import {response} from "@/lib/http";
export function GET(){
 return response({...audit,data_category:"official_operator_map_source_metadata",
 site_connection_feasibility_evaluated:false,operator_approved_mw:null,
 live_feeds:false,not_a_grid_scope_equivalent:true});
}
