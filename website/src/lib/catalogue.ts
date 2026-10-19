import { points, capacities } from "./repository";
import type { Capacity, Point, Paged } from "./types";

/** Read every currently indexed evidence record using the API's bounded pages.
 * Never silently truncate the catalogue when more stations are ingested.
 * A 5,000-row safety limit avoids unbounded server memory consumption.
 */
async function collect<T>(getter:(params:URLSearchParams)=>Promise<Paged<T>>,limit:number):Promise<T[]>{
 const all:T[]=[];
 for(let offset=0;offset<5000;offset+=limit){
  const page=await getter(new URLSearchParams({limit:String(limit),offset:String(offset)}));
  all.push(...page.data);
  if(all.length>=page.pagination.total)return all;
  if(page.data.length===0)throw new Error("EVIDENCE_PAGINATION_EMPTY");
 }
 throw new Error("EVIDENCE_CATALOGUE_TOO_LARGE: use a paginated query rather than dropping records.");
}
export async function evidenceCatalogue():Promise<{stations:Point[];observations:Capacity[]}>{
 const [stations,observations]=await Promise.all([collect(points,100),collect(capacities,200)]);
 return {stations,observations};
}
