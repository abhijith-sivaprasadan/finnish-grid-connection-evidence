import type { Capacity, Point } from "./types";

/**
 * Public, repository-compiled Grid Scope transcription captured 2026-10-17.
 * Original 18 transcriptions were compared with reviewer-supplied Fingrid screenshots
 * on 18-19 October 2026. This is deliberately not a live operator feed,
 * and is served only when DATABASE_READ_URL has not been configured.
 * The figures MUST NOT be treated as connection guarantees or summed.
 */
export const SNAPSHOT_CAPTURE_UTC = "2026-10-17T18:46:43Z";
export const SNAPSHOT_ORIGIN = "https://karttapalaute.fingrid.fi/?link=3opMB&setlanguage=en";
const CATALOG = "https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/";

export const snapshotPoints: Point[] = [
  ["VUOLIJOKI", "VUOLIJOKI"],
  ["ALAPITKA", "ALAPITKÄ"],
  ["ALAJARVI", "ALAJÄRVI"],
  ["SEINAJOKI", "SEINÄJOKI"],
  ["UUSNIVALA", "UUSNIVALA"],
].map(([id, display]) => ({
  connection_point_id: `FI-FINGRID-${id}-400`,
  name: `${display} 400 kV`,
  operator: "Fingrid",
  voltage_kv: 400,
  source_url: CATALOG,
}));

const series: Array<[string, "production" | "consumption", number, number]> = [
  ["VUOLIJOKI", "production", 2026, 500],
  ["VUOLIJOKI", "production", 2030, 500],
  ["VUOLIJOKI", "production", 2035, 500],
  ["ALAPITKA", "production", 2026, 380],
  ["ALAPITKA", "production", 2030, 380],
  ["ALAPITKA", "production", 2035, 380],
  ["ALAJARVI", "production", 2026, 400],
  ["ALAJARVI", "production", 2030, 400],
  ["ALAJARVI", "production", 2035, 400],
  ["SEINAJOKI", "consumption", 2026, 400],
  ["SEINAJOKI", "consumption", 2030, 400],
  ["SEINAJOKI", "consumption", 2035, 400],
  ["UUSNIVALA", "consumption", 2026, 400],
  ["UUSNIVALA", "consumption", 2030, 400],
  ["UUSNIVALA", "consumption", 2035, 400],
  ["VUOLIJOKI", "consumption", 2026, 500],
  ["ALAPITKA", "consumption", 2026, 500],
  ["ALAJARVI", "consumption", 2026, 400],
];

export const snapshotCapacities: Capacity[] = series.map(([id, direction, year, value]) => {
  const point = snapshotPoints.find(p => p.connection_point_id === `FI-FINGRID-${id}-400`);
  if (!point) throw new Error("Unknown compiled point");
  return {
    observation_id: `gs-20261017-${id.toLowerCase()}-400-${direction}-${year}`,
    connection_point_id: point.connection_point_id,
    name: point.name,
    operator: point.operator,
    voltage_kv: point.voltage_kv,
    direction,
    effective_year: year,
    capacity_value: value,
    capacity_unit: "MW",
    capacity_status: "published_indicative",
    source_observed_at: SNAPSHOT_CAPTURE_UTC,
    source_url: SNAPSHOT_ORIGIN,
    validity_notes: "Repository-compiled indicative Fingrid Grid Scope transcription. Publication date not stated. Conditional screening estimate; original 18 values screenshot-matched; not physically validated, no connection rights and not additive across substations.",
    source_published_on: null,
  };
});
