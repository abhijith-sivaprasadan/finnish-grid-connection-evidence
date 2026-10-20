import result from "@/lib/pypsa-extended-sensitivity.json";
import {response} from "@/lib/http";
export function GET(){
 return response({...result,is_operator_confirmed_capacity:false,is_operational_observation:false});
}
