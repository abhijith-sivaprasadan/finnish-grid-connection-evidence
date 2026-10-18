import { readQuery, type ReadQuery } from "./db";
import type { Operation, Capacity } from "./types";

import { FEEDS } from "./workbench-shared";
export { FEEDS, YEARS } from "./workbench-shared";
export type ReviewStatus = "pending_independent_recheck";
export type AuditRecord = Pick<Capacity,"observation_id"|"connection_point_id"|"name"|"direction"|"effective_year"|"capacity_value"|"capacity_unit"|"source_url"|"source_observed_at"|"validity_notes"> & { independent_recheck_status: ReviewStatus };

export function auditRecords(values: Capacity[]): AuditRecord[] {
  return [...values].sort((a,b)=>a.name.localeCompare(b.name)||a.direction.localeCompare(b.direction)||(a.effective_year??0)-(b.effective_year??0))
    .map(value=>({
      observation_id:value.observation_id, connection_point_id:value.connection_point_id,
      name:value.name, direction:value.direction, effective_year:value.effective_year,
      capacity_value:value.capacity_value, capacity_unit:value.capacity_unit, source_url:value.source_url,
      source_observed_at:value.source_observed_at, validity_notes:value.validity_notes,
      independent_recheck_status:"pending_independent_recheck",
    }));
}
function csvCell(v: unknown) {
  const s = v == null ? "" : String(v);
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g,'""') + '"' : s;
}
export function csvTable(columns: readonly string[], rows: Record<string,unknown>[]): string {
  return [columns.join(","),...rows.map(row=>columns.map(column=>csvCell(row[column])).join(","))].join("\r\n")+"\r\n";
}
export function auditWorksheet(values: Capacity[]):string {
  const columns = ["observation_id","connection_point_id","name","direction","effective_year","capacity_value","capacity_unit","source_url","source_observed_at","independent_recheck_status","reviewed_at_utc","reviewer","current_value","current_unit","current_source_url","evidence_reference","finding_notes"];
  return csvTable(columns,auditRecords(values).map(r=>({...r,
    reviewed_at_utc:"", reviewer:"", current_value:"", current_unit:"", current_source_url:"", evidence_reference:"", finding_notes:""})));
}
export function chooseDays(raw: string | string[] | undefined): 1|2|3|7 {
  if (raw===undefined) return 3;
  if (raw==="1"||raw==="2"||raw==="3"||raw==="7") return Number(raw) as 1|2|3|7;
  throw new Error("INVALID_WINDOW");
}
function anchorDay(latestEnd: string): Date {
  const timestamp = Date.parse(latestEnd);
  if (!Number.isFinite(timestamp)) throw new Error("INVALID_LATEST_UTC_INTERVAL");
  // The latest interval often ends precisely at 00:00 UTC the next day.
  // A full-day lookback must anchor on that last completed UTC day.
  const end = new Date(timestamp);
  const midnight = Date.UTC(end.getUTCFullYear(),end.getUTCMonth(),end.getUTCDate());
  return new Date(timestamp===midnight?midnight:midnight+86400000);
}
export function boundsFromLatest(latestEnd:string,days:1|2|3|7) {
  const to=anchorDay(latestEnd), from=new Date(to.getTime()-days*86400000);
  return {from:from.toISOString().replace(/Z$/, "000Z"),to:to.toISOString().replace(/Z$/, "000Z"),days};
}
export async function operationalWindow(latestEnd:string,days:1|2|3|7,query:ReadQuery=readQuery) {
  const window=boundsFromLatest(latestEnd,days);
  const data=await query<Operation & Record<string,unknown>>(
    `SELECT source,dataset_id,metric,value,unit,timestamp_utc,interval_end_utc,retrieved_at,source_url,area
     FROM latest_operational
     WHERE timestamp_utc >= $1 AND timestamp_utc < $2
       AND ((source='fingrid' AND dataset_id IN ('124','74')) OR (source='entsoe' AND dataset_id='A65'))
     ORDER BY timestamp_utc ASC, source ASC, dataset_id ASC
     LIMIT 2100`,[window.from,window.to]);
  // One row per quarter-hour per feed across at most seven full days.
  // Refuse accidental caps rather than silently present a partial chart.
  if(data.length>=2100) throw new Error("OPERATION_WINDOW_LIMIT");
  return {window,data};
}
export type QualityRow = {
  source:string; dataset_id:string; day_utc:string;
  intervals:number; stored_rows:number; revisions:number; gaps:number;
  first_start:string; last_end:string; latest_retrieved:string;
  complete:boolean;
};
type QualitySqlRow = {
  source:string; dataset_id:string; day_utc:string; intervals:number|string;
  stored_rows:number|string; gaps:number|string; first_start:string;
  last_end:string; latest_retrieved:string;
};
const fullDayStart = (day:string)=>day+"T00:00:00";
const normalizeTime = (timestamp:string)=>Date.parse(timestamp);
export function assessQuality(rows:QualitySqlRow[]):QualityRow[] {
  return rows.map(row=>{
    const intervals=Number(row.intervals),stored_rows=Number(row.stored_rows),gaps=Number(row.gaps);
    const from=normalizeTime(row.first_start), to=normalizeTime(row.last_end);
    const begin=Date.parse(fullDayStart(row.day_utc)+"Z");
    const coverage=Number.isFinite(from)&&Number.isFinite(to)&&
      from===begin&&to===begin+86400000;
    const correctCount=row.source==="fingrid" ? intervals===96 : intervals>0;
    return {...row,intervals,stored_rows,revisions:stored_rows-intervals,gaps,
      complete:coverage&&gaps===0&&correctCount};
  }).sort((a,b)=>b.day_utc.localeCompare(a.day_utc)||a.source.localeCompare(b.source)||a.dataset_id.localeCompare(b.dataset_id));
}
export async function qualityReport(latestEnd:string,query:ReadQuery=readQuery) {
  const end=anchorDay(latestEnd);
  const start=new Date(end.getTime()-30*86400000);
  const rows=await query<QualitySqlRow & Record<string,unknown>>(
    `WITH observed AS (
       SELECT source,dataset_id,area,timestamp_utc,interval_end_utc,retrieved_at,
        row_number() OVER (PARTITION BY source,dataset_id,area,timestamp_utc,interval_end_utc ORDER BY retrieved_at DESC) AS revision_rank,
        count(*) OVER (PARTITION BY source,dataset_id,area,timestamp_utc,interval_end_utc) AS revision_count
       FROM operational_series
       WHERE timestamp_utc >= $1 AND timestamp_utc < $2
         AND ((source='fingrid' AND dataset_id IN ('124','74')) OR (source='entsoe' AND dataset_id='A65'))
     ), ordered AS (
       SELECT source,dataset_id,substring(timestamp_utc,1,10) AS day_utc,
         timestamp_utc,interval_end_utc,retrieved_at,revision_count,
         lag(interval_end_utc) OVER (
           PARTITION BY source,dataset_id,substring(timestamp_utc,1,10)
           ORDER BY timestamp_utc,interval_end_utc) AS previous_end
       FROM observed WHERE revision_rank=1
     )
     SELECT source,dataset_id,day_utc,
       count(*)::integer AS intervals,
       sum(revision_count)::integer AS stored_rows,
       sum(CASE WHEN previous_end IS NOT NULL AND previous_end <> timestamp_utc THEN 1 ELSE 0 END)::integer AS gaps,
       min(timestamp_utc) AS first_start,max(interval_end_utc) AS last_end,
       max(retrieved_at) AS latest_retrieved
     FROM ordered
     GROUP BY source,dataset_id,day_utc
     ORDER BY day_utc DESC,source,dataset_id LIMIT 93`,[start.toISOString().replace(/Z$/, "000Z"),end.toISOString().replace(/Z$/, "000Z")]);
  const data=assessQuality(rows);
  const sources=FEEDS.map(feed=>({
    ...feed, recordedDays:data.filter(d=>d.source===feed.source&&d.dataset_id===feed.dataset_id).length,
    completeDays:data.filter(d=>d.source===feed.source&&d.dataset_id===feed.dataset_id&&d.complete).length,
    uniqueIntervals:data.filter(d=>d.source===feed.source&&d.dataset_id===feed.dataset_id).reduce((n,d)=>n+d.intervals,0),
    retrievalRevisions:data.filter(d=>d.source===feed.source&&d.dataset_id===feed.dataset_id).reduce((n,d)=>n+d.revisions,0)
  }));
  return {from:start.toISOString(),to:end.toISOString(),days:30,rows:data,sources,
    rawRows:data.reduce((n,r)=>n+r.stored_rows,0),
    distinctIntervals:data.reduce((n,r)=>n+r.intervals,0),
    retrievalRevisions:data.reduce((n,r)=>n+r.revisions,0),
    disclaimer:"Historical source coverage and retrieval versions, not live SCADA or capacity at a substation."};
}
