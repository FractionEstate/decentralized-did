#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_HOST="${API_HOST:-127.0.0.1}"
MOCK_API_PORT="${MOCK_API_PORT:-8002}"
PLAYWRIGHT_BROWSERS="${PLAYWRIGHT_BROWSERS:-chromium,firefox,webkit}"
API_URL="http://${API_HOST}:${MOCK_API_PORT}"

export API_URL
export PLAYWRIGHT_BROWSERS

start_mock_api() {
  local log_file
  log_file="${ROOT_DIR}/.tmp/mock-api.log"
  mkdir -p "$(dirname "$log_file")"
  python3 -m uvicorn api_server_mock:app --host "${API_HOST}" --port "${MOCK_API_PORT}" --log-level info >"${log_file}" 2>&1 &
  MOCK_API_PID=$!
}

stop_mock_api() {
  if [[ -n "${MOCK_API_PID:-}" ]]; then
    kill "${MOCK_API_PID}" >/dev/null 2>&1 || true
  fi
}

wait_for_api() {
  local retries=30
  local delay=1
  for ((i=0; i<retries; i++)); do
    if curl -sSf "${API_URL}/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
  done
  echo "Mock API did not become ready at ${API_URL}" >&2
  return 1
}

trap stop_mock_api EXIT

start_mock_api
wait_for_api

cd "${ROOT_DIR}/demo-wallet"

npx playwright test "$@"
