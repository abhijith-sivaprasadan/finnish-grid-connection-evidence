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
check 503 "/api/v1/overview"
grep -q "SOURCE_UNAVAILABLE" /tmp/grid-smoke-response.json
check 503 "/api/v1/health"
grep -q '"status":"degraded"' /tmp/grid-smoke-response.json
check 200 "/"
grep -q "temporarily unavailable" /tmp/grid-smoke-response.json
echo "All no-secret production route smoke checks passed."
