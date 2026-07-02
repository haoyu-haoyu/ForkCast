#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${FORKCAST_PREFLIGHT_PORT:-4174}"
SERVER_PID=""
SERVER_LOG="${TMPDIR:-/tmp}/forkcast-preflight-server.log"

fail() {
  echo "NO-GO: $*" >&2
  exit 1
}

cleanup() {
  if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT
trap 'fail "line ${LINENO}: ${BASH_COMMAND}"' ERR

echo "ForkCast demo preflight"
echo "Repository: ${ROOT}"

if [[ -n "$(git -C "${ROOT}" status --porcelain --untracked-files=all)" ]]; then
  git -C "${ROOT}" status --short
  fail "git working tree is not clean"
fi
echo "PASS git clean"

unset DEEPSEEK_API_KEY
unset LLM_API_KEY
unset OPENAI_API_KEY

echo "Running Python test suite..."
(cd "${ROOT}" && uv run pytest -q)
echo "PASS pytest"

echo "Running dashboard tests..."
(cd "${ROOT}/web" && npm test)
echo "PASS npm test"

echo "Building offline cached dashboard..."
(cd "${ROOT}/web" && npm run build)
echo "PASS npm run build"

[[ -f "${ROOT}/web/dist/index.html" ]] || fail "web/dist/index.html missing after build"
grep -R "Policy Impact Sandbox" "${ROOT}/web/dist" >/dev/null || fail "built demo missing title text"
grep -R "Human grading" "${ROOT}/web/dist" >/dev/null || fail "built demo missing human grading text"
grep -R "f553f7bfd73b1ed81b" "${ROOT}/web/dist" >/dev/null || fail "built demo missing Kaspa f553 anchor"
echo "PASS cached demo strings"

echo "Serving static offline demo on http://127.0.0.1:${PORT}/ ..."
python3 -m http.server "${PORT}" --bind 127.0.0.1 --directory "${ROOT}/web/dist" >"${SERVER_LOG}" 2>&1 &
SERVER_PID="$!"
sleep 1
if ! kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
  sed -n '1,120p' "${SERVER_LOG}" >&2 || true
  fail "offline static server failed to start"
fi

curl -fsS "http://127.0.0.1:${PORT}/" | grep -q 'id="root"' || fail "offline dashboard root did not serve"
echo "PASS offline cached demo serves"

echo "GO: ForkCast demo preflight passed"
