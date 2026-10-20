import study from "@/lib/pypsa-verified-seasonal-2025.json";
import {response} from "@/lib/http";
export function GET(){
 return response({...study,is_operator_confirmed_capacity:false,is_operational_observation:false});
}
