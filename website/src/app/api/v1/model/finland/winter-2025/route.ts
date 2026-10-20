import result from "@/lib/pypsa-long-winter-2025.json";
import {response} from "@/lib/http";
export function GET(){return response({...result,operator_confirmed_capacity:false});}
