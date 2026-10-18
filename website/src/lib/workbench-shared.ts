/** Pure client-safe labels and source identity (no database imports). */
export const FEEDS = [
  { source: "fingrid", dataset_id: "124", metric: "electricity_consumption", label: "Fingrid · Consumption", unit: "MWh/h" },
  { source: "fingrid", dataset_id: "74", metric: "electricity_production", label: "Fingrid · Production", unit: "MWh/h" },
  { source: "entsoe", dataset_id: "A65", metric: "electricity_consumption", label: "ENTSO-E · Actual load", unit: "MW" },
] as const;
export type Feed = (typeof FEEDS)[number];
export const YEARS = [2026, 2030, 2035] as const;
