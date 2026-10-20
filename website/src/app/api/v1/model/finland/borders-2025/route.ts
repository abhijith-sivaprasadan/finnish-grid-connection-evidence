import result from "@/lib/pypsa-border-observed-2025.json";
import {response} from "@/lib/http";
export function GET(){return response({...result,operator_confirmed_capacity:false,guaranteed_import_rights:false});}
