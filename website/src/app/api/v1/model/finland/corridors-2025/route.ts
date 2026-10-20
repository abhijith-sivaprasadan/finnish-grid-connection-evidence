import data from "@/lib/pypsa-zonal-2025.json";
import {response} from "@/lib/http";
export function GET(){
 return response({...data,operator_confirmed_connection_capacity:false,is_physical_ac_dc_power_flow:false});
}
