#!/usr/bin/env bash
set -euo pipefail
# Test the BUILT production server without any DB URL or tokens.
unset DATABASE_READ_URL || true
port=3189
npm run start -- --port "$port" > /tmp/finnish-grid-atlas-smoke.log 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
for i in $(seq 1 45); do
  if curl -s --max-time 2 "http://127.0.0.1:$port/method" >/dev/null; then break; fi
  sleep 1
done

check() {
  local expected="$1" path="$2"
  local got
  got=$(curl -sS --max-time 8 -o /tmp/grid-smoke-response.json -w '%{http_code}' "http://127.0.0.1:$port$path")
  if [ "$got" != "$expected" ]; then
    echo "Unexpected HTTP status for $path: $got (wanted $expected)"
    exit 1
  fi
  echo "PASS HTTP $expected $path"
}
check 200 "/method"
check 200 "/api"
check 200 "/api/openapi.json"
grep -q '"openapi":"3.1.0"' /tmp/grid-smoke-response.json
check 400 "/api/v1/capacity?direction=INVALID"
grep -q "INVALID_QUERY" /tmp/grid-smoke-response.json
check 400 "/api/v1/operations?source=fingrid&dataset_id=A65"
check 200 "/api/v1/overview"
grep -q '"data_mode":"compiled_snapshot"' /tmp/grid-smoke-response.json
check 200 "/api/v1/points"
grep -q 'FI-FINGRID-ALAPITKA-400' /tmp/grid-smoke-response.json
check 200 "/api/v1/capacity?direction=production&year=2030"
grep -q '"capacity_status":"published_indicative"' /tmp/grid-smoke-response.json
check 200 "/api/v1/coverage"
grep -q '"missing_in_compiled_capture":12' /tmp/grid-smoke-response.json
check 200 "/connections"
grep -q "Download independent audit worksheet" /tmp/grid-smoke-response.json
check 200 "/api/v1/quality"
grep -q '"data_mode":"compiled_snapshot"' /tmp/grid-smoke-response.json
check 200 "/api/v1/source-review"
grep -q '"screenshot_matches":18' /tmp/grid-smoke-response.json
grep -q '"exact_tooltips":17' /tmp/grid-smoke-response.json
grep -q '"explicit_panel_numbers":1' /tmp/grid-smoke-response.json
grep -q '"physically_validated_connection_capacity":false' /tmp/grid-smoke-response.json
check 200 "/api/v1/export/recheck"
grep -q "pending_independent_recheck" /tmp/grid-smoke-response.json
test "$(grep -c 'pending_independent_recheck' /tmp/grid-smoke-response.json)" = 18
check 200 "/quality"
grep -q "18 original source observations" /tmp/grid-smoke-response.json
check 200 "/operations?days=2"
check 503 "/api/v1/health"
grep -q '"status":"degraded"' /tmp/grid-smoke-response.json
check 200 "/"
grep -q "Compiled source snapshot" /tmp/grid-smoke-response.json
grep -q "Electricity grid" /tmp/grid-smoke-response.json
grep -q "RESEARCH WORKSPACE" /tmp/grid-smoke-response.json
echo "All no-secret production route and public snapshot smoke checks passed."
