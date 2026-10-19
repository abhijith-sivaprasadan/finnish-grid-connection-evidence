import { readQuery, type ReadQuery } from "./db";
import { snapshotPoints, snapshotCapacities } from "./snapshot";
import { directionParam, operationsParams, pageParams, pointParam, yearParam } from "./params";
import type { Capacity, Operation, Overview, Paged, Point } from "./types";
import { REVIEWED_SAMPLE_SIZE, EXACT_TOOLTIP_COUNT, PANEL_VALUE_COUNT } from "./verification";

export const CAPACITY_CAUTION =
  "Original 18 Fingrid Grid Scope transcriptions matched reviewer-supplied screenshots on 18-19 October 2026. This is NOT operator-confirmed capacity, grid feasibility, or guaranteed headroom. Missing entries are unknown, not zero; values cannot be added.";
export const OPERATIONS_CAUTION =
  "National operational context, not substation telemetry or available connection headroom.";

const DATA_KEYS = "observation_id, connection_point_id, name, operator, voltage_kv, direction, effective_year, capacity_value, capacity_unit, capacity_status, source_observed_at, source_url, validity_notes, source_published_on";
const OP_KEYS = "source, dataset_id, metric, value, unit, timestamp_utc, interval_end_utc, retrieved_at, source_url, area";

// Do not silently serve a snapshot if an explicitly configured database fails.
// Injectable query functions continue to work unmodified in tests and audits.
const useCompiledSnapshot = (query: ReadQuery) => query === readQuery && !process.env.DATABASE_READ_URL;

export async function overview(query: ReadQuery = readQuery): Promise<Overview> {
  if (useCompiledSnapshot(query)) return {
    points:snapshotPoints.length,capacity_observations:snapshotCapacities.length,
    operational_rows_stored:0,newest_operational_interval_utc:null,
    source_values_independently_verified:false,
    source_transcription_screenshot_review:{matched:REVIEWED_SAMPLE_SIZE,exact_tooltips:EXACT_TOOLTIP_COUNT,explicit_panel_numbers:PANEL_VALUE_COUNT,review_date:"2026-10-19"},
    operator_confirmed_connection_capacity:false,data_mode:"compiled_snapshot",
  };
  const rows = await query<{
    points: string | number; capacity_observations: string | number;
    operational_rows_stored: string | number; newest_operational_interval_utc: string | null;
  }>("SELECT (SELECT count(*) FROM connection_point) AS points, (SELECT count(*) FROM capacity_observation WHERE capacity_status = 'published_indicative') AS capacity_observations, (SELECT count(*) FROM operational_series) AS operational_rows_stored, (SELECT MAX(interval_end_utc) FROM latest_operational) AS newest_operational_interval_utc");
  const row = rows[0];
  return {points: Number(row?.points || 0), capacity_observations: Number(row?.capacity_observations || 0),
    operational_rows_stored: Number(row?.operational_rows_stored || 0),
    newest_operational_interval_utc: row?.newest_operational_interval_utc ?? null,
    source_values_independently_verified: false,
    source_transcription_screenshot_review:{matched:REVIEWED_SAMPLE_SIZE,exact_tooltips:EXACT_TOOLTIP_COUNT,explicit_panel_numbers:PANEL_VALUE_COUNT,review_date:"2026-10-19"},
    operator_confirmed_connection_capacity:false,data_mode:"neon"};
}
export async function points(params = new URLSearchParams(), query: ReadQuery = readQuery): Promise<Paged<Point>> {
  const {limit, offset} = pageParams(params, 100);
  if (useCompiledSnapshot(query)) return {
    data:snapshotPoints.slice(offset,offset+limit),
    pagination:{total:snapshotPoints.length,limit,offset},limitations:[CAPACITY_CAUTION],data_mode:"compiled_snapshot",
  };
  const [count] = await query<{total: string | number}>("SELECT count(*) AS total FROM connection_point");
  const rows = await query<Point & Record<string, unknown>>(
    "SELECT connection_point_id,name,operator,voltage_kv,source_url FROM connection_point ORDER BY name LIMIT $1 OFFSET $2",[limit,offset]);
  return {data:rows,pagination:{total:Number(count?.total||0),limit,offset},limitations:[CAPACITY_CAUTION]};
}
export async function point(id: string, query: ReadQuery = readQuery): Promise<Point | null> {
  if (!/^FI-FINGRID-[A-Z0-9-]{3,60}$/.test(id)) return null;
  if (useCompiledSnapshot(query)) return snapshotPoints.find(p=>p.connection_point_id===id)??null;
  const rows = await query<Point & Record<string, unknown>>(
    "SELECT connection_point_id,name,operator,voltage_kv,source_url FROM connection_point WHERE connection_point_id = $1",[id]);
  return rows[0] || null;
}
export async function capacities(params = new URLSearchParams(), query: ReadQuery = readQuery): Promise<Paged<Capacity>> {
  const { limit, offset } = pageParams(params, 200);
  const direction = directionParam(params), year = yearParam(params), pt = pointParam(params);
  if (useCompiledSnapshot(query)) {
    const match=snapshotCapacities.filter(c=>(!direction||c.direction===direction)&&
      (year===null||c.effective_year===year)&&(!pt||c.connection_point_id===pt));
    return {data:match.slice(offset,offset+limit),pagination:{total:match.length,limit,offset},
      limitations:[CAPACITY_CAUTION],data_mode:"compiled_snapshot"};
  }
  const predicates: string[] = [], values: unknown[] = [];
  if (direction) { values.push(direction); predicates.push("direction = $" + values.length); }
  if (year) { values.push(year); predicates.push("effective_year = $" + values.length); }
  if (pt) { values.push(pt); predicates.push("connection_point_id = $" + values.length); }
  const where = predicates.length ? " WHERE " + predicates.join(" AND ") : "";
  const [count] = await query<{total: number | string}>("SELECT count(*) AS total FROM published_capacity" + where,values);
  const rows = await query<Capacity & Record<string, unknown>>(
    "SELECT " + DATA_KEYS + " FROM published_capacity" + where +
    " ORDER BY name,direction,effective_year,source_observed_at DESC LIMIT $" + (values.length+1) +
    " OFFSET $" + (values.length+2), [...values,limit,offset]);
  return {data:rows,pagination:{total:Number(count?.total||0),limit,offset},limitations:[CAPACITY_CAUTION]};
}
export async function operations(params = new URLSearchParams(), query: ReadQuery = readQuery, now = new Date()): Promise<Paged<Operation>> {
  const {limit,offset,source,dataset,from,to} = operationsParams(params, now);
  const values: unknown[] = [from,to], predicates = ["timestamp_utc >= $1","timestamp_utc < $2"];
  if (source) { values.push(source); predicates.push("source = $" + values.length); }
  if (dataset) { values.push(dataset); predicates.push("dataset_id = $" + values.length); }
  const where=" WHERE "+predicates.join(" AND ");
  const [count]=await query<{total:number|string}>("SELECT count(*) AS total FROM latest_operational"+where,values);
  const rows=await query<Operation & Record<string,unknown>>(
    "SELECT "+OP_KEYS+" FROM latest_operational"+where+
    " ORDER BY timestamp_utc DESC, source, dataset_id LIMIT $"+(values.length+1)+
    " OFFSET $"+(values.length+2), [...values,limit,offset]);
  return {data:rows,pagination:{total:Number(count?.total||0),limit,offset},limitations:[OPERATIONS_CAUTION]};
}
export async function coverage(params=new URLSearchParams(), query: ReadQuery=readQuery) {
  const year=yearParam(params);
  const years=year ? [year] : [2026,2030,2035];
  const [ps, obs]: [Point[], Capacity[]] = useCompiledSnapshot(query)
    ? [snapshotPoints, snapshotCapacities] : await Promise.all([
    query<Point & Record<string,unknown>>(
      "SELECT connection_point_id,name,operator,voltage_kv,source_url FROM connection_point ORDER BY name"),
    query<Capacity & Record<string,unknown>>(
      "SELECT "+DATA_KEYS+" FROM published_capacity ORDER BY source_observed_at DESC"),
  ]);
  const rows = [];
  for (const p of ps) for(const direction of ["consumption","production"] as const)
    for(const effective_year of years) {
      const candidates=obs.filter(o=>o.connection_point_id===p.connection_point_id &&
        o.direction===direction && Number(o.effective_year)===effective_year);
      rows.push({connection_point_id:p.connection_point_id, name:p.name, direction, year:effective_year,
        status:candidates.length===0?"not_in_compiled_capture":
               candidates.length===1?"published_indicative":"needs_reconciliation",
        value:candidates.length===1?candidates[0].capacity_value:null,
        unit:candidates.length===1?candidates[0].capacity_unit:null,
        source_observed_at:candidates.length===1?candidates[0].source_observed_at:null});
    }
  return {data:rows,limitations:[CAPACITY_CAUTION],coverage:{
    intersections:rows.length,published:rows.filter(r=>r.status==="published_indicative").length,
    missing_in_compiled_capture:rows.filter(r=>r.status==="not_in_compiled_capture").length,
    needs_reconciliation:rows.filter(r=>r.status==="needs_reconciliation").length},
    data_mode:useCompiledSnapshot(query)?"compiled_snapshot":"neon"};
}
