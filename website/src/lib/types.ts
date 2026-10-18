export type Direction = "production" | "consumption";
export type Source = "fingrid" | "entsoe";
export type Point = {
  connection_point_id: string;
  name: string;
  operator: string;
  voltage_kv: number | null;
  source_url: string;
};
export type Capacity = {
  observation_id: string;
  connection_point_id: string;
  name: string;
  operator: string;
  voltage_kv: number | null;
  direction: Direction;
  effective_year: number | null;
  capacity_value: number;
  capacity_unit: "MW" | "MVA";
  capacity_status: "published_indicative";
  source_observed_at: string;
  source_url: string;
  validity_notes: string;
  source_published_on: string | null;
};
export type Operation = {
  source: Source;
  dataset_id: string;
  metric: string;
  value: number;
  unit: string;
  timestamp_utc: string;
  interval_end_utc: string;
  retrieved_at: string;
  source_url: string;
  area: "FI";
};
export type Overview = {
  points: number;
  capacity_observations: number;
  operational_rows_stored: number;
  newest_operational_interval_utc: string | null;
  source_values_independently_verified: false;
};
export type Pagination = { total: number; limit: number; offset: number };
export type Paged<T> = { data: T[]; pagination: Pagination; limitations: string[] };
