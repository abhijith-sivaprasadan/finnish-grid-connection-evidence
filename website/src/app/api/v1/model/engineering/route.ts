import data from "@/lib/krios-engineering-verified-2026.json";
import {response} from "@/lib/http";
export function GET(){
 return response({...data,data_category:"independent_CIGRE_and_FI_regional_hypothetical_model_results",
   operator_approved_site_mw:null,actual_fingrid_2025_AC_calibration_complete:false,
   CIGRE_reference_is_a_real_Finnish_or_Dutch_site:false,
   all_model_data_are_dated_snapshot:true});
}
