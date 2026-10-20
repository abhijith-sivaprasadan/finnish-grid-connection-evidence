import { response } from "@/lib/http";
export async function GET() {
  const q = (name:string,desc:string) => ({name,in:"query",required:false,description:desc,schema:{type:"string"}});
  const paging=[
    {name:"limit",in:"query",schema:{type:"integer",minimum:1,maximum:500},required:false},
    {name:"offset",in:"query",schema:{type:"integer",minimum:0,maximum:100000},required:false}
  ];
  const success={description:"Source-backed JSON; see limitations and pagination in response."};
  const errors={400:{description:"Invalid filter"},503:{description:"Evidence database unavailable"}};
  return response({
    openapi:"3.1.0",info:{title:"Finnish Grid Atlas Read-only API",version:"1.0.0",
      description:"Public read-only research evidence. Indicative source transcriptions are NOT operator-verified headroom. No additive capacity or network-studies claim."},
    servers:[{url:"/"}],
    paths:{
      "/api/v1/model/finland/seasons":{get:{summary:"Three equal 14-day verified historical winter/summer/autumn PyPSA studies with honest 2025 missing-source coverage, not full year or grid feasibility",responses:{200:success}}},
      "/api/v1/model/finland/sensitivity":{get:{summary:"Thirty-day Fingrid-observed historical input and solver-verified hypothetical PyPSA parameter scenarios, not capacity or forecasts",responses:{200:success}}},
      "/api/v1/model/finland":{get:{summary:"Historical PyPSA Finland scenario output (modelled assumptions, no substation connectability claim)",responses:{200:success}}},
      "/api/v1/overview":{get:{summary:"Evidence counts and freshness",responses:{200:success,503:errors[503]}}},
      "/api/v1/health":{get:{summary:"Database availability",responses:{200:success,503:errors[503]}}},
      "/api/v1/points":{get:{summary:"Connection points",parameters:paging,responses:{200:success,...errors}}},
      "/api/v1/points/{id}":{get:{summary:"One named point",parameters:[{name:"id",in:"path",required:true,schema:{type:"string"}}],responses:{200:success,404:{description:"Unknown point"},503:errors[503]}}},
      "/api/v1/capacity":{get:{summary:"Published indicative estimates; no interpolation",
        parameters:[...paging,q("direction","production or consumption"),
          q("point_id","One supported connection point ID"),q("year","Published effective year")],
        responses:{200:success,...errors}}},
      "/api/v1/screening":{get:{summary:"Source-evidence screening; not confirmed connectability",parameters:[q("demand_mw","Positive requested consumption in MW, up to 10000; default 100"),q("year","Exact effective year, default 2030"),q("direction","consumption only in v1"),q("voltage","all, 110, 220 or 400; sample filter, not national coverage")],responses:{200:success,...errors}}},
      "/api/v1/coverage":{get:{summary:"Compiled snapshot coverage: missing does not mean zero",
        parameters:[q("year","An optional year, default the three explicitly compared source years")],
        responses:{200:success,...errors}}},
      "/api/v1/source-review":{get:{summary:"18-row original screenshot-match audit metadata (not grid validation)",responses:{200:success}}},
      "/api/v1/quality":{get:{summary:"Source-day continuity, distinct intervals and retrieval revision counts; 30-day bounded read",responses:{200:success,503:errors[503]}}},
      "/api/v1/export/recheck":{get:{summary:"18-row CSV reviewer worksheet; all observations pending independent recheck",responses:{200:{description:"Provenance-preserving CSV download"},503:errors[503]}}},
      "/api/v1/operations":{get:{summary:"Latest revisions of national operational intervals",
        parameters:[...paging,q("source","fingrid or entsoe"),q("dataset_id","124, 74 or A65"),
          q("from","ISO timestamp with timezone; maximum 31-day window"),
          q("to","ISO timestamp with timezone")],
        responses:{200:success,...errors}}}
    },
    components:{schemas:{Error:{type:"object",properties:{error:{type:"object",
      properties:{code:{type:"string"},message:{type:"string"}}}}}}},
  });
}
