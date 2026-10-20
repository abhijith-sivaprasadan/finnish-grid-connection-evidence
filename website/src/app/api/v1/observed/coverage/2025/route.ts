import data from "@/lib/fingrid-archive-coverage-2025.json";
import {response} from "@/lib/http";
export function GET(){
 return response({...data,data_kind:"observed_source_coverage_summary",
  is_calendar_year_source_complete:false,is_operational_grid_capacity:false,
  is_modelled_2030_forecast:false});
}
