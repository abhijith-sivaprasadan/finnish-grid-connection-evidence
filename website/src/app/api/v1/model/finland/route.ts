import model from "@/lib/pypsa-scenario-results.json";
import {response} from "@/lib/http";
export const runtime="nodejs";
export function GET(){
 return response({...model,data_category:"model_scenario",is_operational_observation:false,
  is_operator_confirmed_capacity:false});
}
