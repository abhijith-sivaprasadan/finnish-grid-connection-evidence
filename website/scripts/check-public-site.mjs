#!/usr/bin/env node
/**
 * Black-box production availability and evidence-integrity check.
 * Uses public endpoints only. Never needs database URLs or API keys.
 * Production workflow enforces live Neon now that its reader has been verified.
 * Local runs without EXPECT_LIVE_DB=true still accept an explicit snapshot.
 */
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

const base = (process.env.ATLAS_PUBLIC_URL || "https://finnish-grid-atlas.vercel.app").replace(/\/$/, "");
const requireLive = process.env.EXPECT_LIVE_DB === "true";
const maxAgeHours = Number(process.env.MAX_OPERATIONAL_AGE_HOURS || "168");

export function evaluateEvidence(data, { requireLive = false, maxAgeHours = 168, now = Date.now() } = {}) {
  assert.ok(data && Number.isInteger(data.points) && data.points > 0, "No known connection points");
  assert.ok(Number.isInteger(data.capacity_observations) && data.capacity_observations > 0, "No capacity records");
  assert.ok(data.data_mode === "neon" || data.data_mode === "compiled_snapshot", "Unrecognized data mode");
  assert.equal(data.source_values_independently_verified, false, "Site unexpectedly labels all transcriptions verified");
  if (requireLive) {
    assert.equal(data.data_mode, "neon", "Expected Neon but public site still serves compiled snapshot");
    assert.ok(data.operational_rows_stored > 0, "Neon appears connected but has no operational rows");
    assert.ok(data.newest_operational_interval_utc, "Live store has no latest UTC interval");
    const parsed = Date.parse(data.newest_operational_interval_utc);
    assert.ok(Number.isFinite(parsed), "Bad UTC interval timestamp");
    const ageHours = (now - parsed) / 3_600_000;
    assert.ok(ageHours >= -1, "Unexpected future operational interval");
    assert.ok(ageHours <= maxAgeHours, `Operational data stale: ${ageHours.toFixed(1)} h`);
  }
  return { mode: data.data_mode, points: data.points, observations: data.capacity_observations };
}

async function get(path, { codes = [200] } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const res = await fetch(base + path, { headers: { "user-agent": "grid-atlas-public-monitor/1.0" }, signal: controller.signal, redirect: "follow" });
    assert.ok(codes.includes(res.status), `${path}: unexpected HTTP ${res.status}`);
    return res;
  } finally { clearTimeout(timer); }
}

export async function checkPublicSite() {
  assert.ok(/^https:\/\//.test(base), "Public URL must be HTTPS");
  if (!Number.isFinite(maxAgeHours) || maxAgeHours <= 0) throw new Error("Invalid MAX_OPERATIONAL_AGE_HOURS");
  for (const path of ["/", "/connections", "/method", "/api", "/api/openapi.json"]) {
    await get(path);
    console.log(`OK ${path}`);
  }
  const summary = await (await get("/api/v1/overview")).json();
  const assessed = evaluateEvidence(summary, { requireLive, maxAgeHours });
  console.log(`Evidence mode ${assessed.mode}; ${assessed.points} points; ${assessed.observations} source observations.`);
  const health = await get("/api/v1/health", { codes: requireLive ? [200] : [200,503] });
  const healthPayload = await health.json();
  if (requireLive) assert.equal(healthPayload.status, "ok", "Read-only database is not healthy");
  if (!requireLive && health.status === 503) console.log("Database not configured: recorded as snapshot-only, not a healthy live DB.");
  if (requireLive) {
    for (const feed of [
      { source: "fingrid", id: "124", metric: "electricity_consumption", unit: "MWh/h" },
      { source: "fingrid", id: "74", metric: "electricity_production", unit: "MWh/h" },
      { source: "entsoe", id: "A65", metric: "electricity_consumption", unit: "MW" },
    ]) {
      const qs = new URLSearchParams({ source: feed.source, dataset_id: feed.id, limit: "1" });
      const payload = await (await get("/api/v1/operations?" + qs)).json();
      assert.ok(Array.isArray(payload.data) && payload.data.length > 0,
        "No operational rows for " + feed.source + " " + feed.id);
      const row = payload.data[0];
      assert.equal(row.source, feed.source, "Wrong source for " + feed.id);
      assert.equal(row.dataset_id, feed.id, "Wrong dataset for " + feed.id);
      assert.equal(row.metric, feed.metric, "Wrong metric for " + feed.id);
      assert.equal(row.unit, feed.unit, "Unexpected unit for " + feed.id);
      assert.ok(Number.isFinite(row.value), "Non-numeric value for " + feed.id);
      assert.ok(/^https:\/\//.test(row.source_url), "Missing HTTPS source for " + feed.id);
      const latest = Date.parse(row.interval_end_utc);
      assert.ok(Number.isFinite(latest), "Missing interval end for " + feed.id);
      const age = (Date.now() - latest) / 3_600_000;
      assert.ok(age >= -1 && age <= maxAgeHours,
        "Dataset " + feed.id + " is stale: " + age.toFixed(1) + " h");
      console.log("OK " + feed.source + " " + feed.id + ": source-linked, unit checked, " + age.toFixed(1) + " h old");
    }
  }
  console.log("Public site monitoring completed.");
}

if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) {
  checkPublicSite().catch(error => { console.error("SITE_MONITOR_FAILURE:", error.message); process.exitCode = 1; });
}
