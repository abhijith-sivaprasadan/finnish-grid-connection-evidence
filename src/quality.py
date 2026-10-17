"""Quality gates distinguish numerical evidence, optional sources, and scientific validation."""
from datetime import datetime, timezone, timedelta


def report(conn):
    counts = {table: conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
              for table in ("connection_point", "capacity_observation", "operational_series", "grid_project", "scenario_result")}
    numeric_count = conn.execute("SELECT count(*) FROM capacity_observation WHERE capacity_value IS NOT NULL AND capacity_unit IS NOT NULL").fetchone()[0]
    has_fingrid = bool(conn.execute("SELECT 1 FROM operational_series WHERE source='fingrid' LIMIT 1").fetchone())
    has_entsoe = bool(conn.execute("SELECT 1 FROM operational_series WHERE source='entsoe' LIMIT 1").fetchone())
    issues = []
    if numeric_count < 5:
        issues.append("Fewer than five numeric published capacity observations are loaded")
    if not has_fingrid:
        issues.append("No live Fingrid operational data has been imported (MVP prerequisite)")
    if not has_entsoe:
        issues.append("No live ENTSO-E operational data has been imported (optional MVP extension)")
    if conn.execute("PRAGMA foreign_key_check").fetchall():
        issues.append("Foreign-key integrity errors")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    if conn.execute("SELECT 1 FROM capacity_observation WHERE source_observed_at < ? LIMIT 1", (cutoff,)).fetchone():
        issues.append("Some capacity snapshots are older than 90 days; this is a review flag, not an expiry rule")
    gaps = 0
    previous = {}
    for row in conn.execute("SELECT * FROM latest_operational ORDER BY source,dataset_id,metric,timestamp_utc"):
        key = (row["source"], row["dataset_id"], row["metric"], row["area"])
        start = datetime.fromisoformat(row["timestamp_utc"])
        end = datetime.fromisoformat(row["interval_end_utc"])
        if key in previous and start != previous[key]:
            gaps += 1
        previous[key] = end
    if gaps:
        issues.append(f"Operational series contain {gaps} gaps or overlaps; no values were interpolated")
    return {"counts": counts, "numeric_capacity_observations": numeric_count,
            "issues": issues, "live_context_ready": has_fingrid,
            "entsoe_optional_ready": has_entsoe,
            "mvp_data_ready": numeric_count >= 5 and has_fingrid and not conn.execute("PRAGMA foreign_key_check").fetchall()}
