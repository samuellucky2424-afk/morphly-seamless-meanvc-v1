#!/usr/bin/env bash
set -euo pipefail

MODEL_PORT="${MODEL_SERVER_PORT:-18000}"
LOG_DIR="/var/log/morphly"
LOG_FILE="${MODEL_LOG_FILE:-${LOG_DIR}/backend.log}"

mkdir -p "$LOG_DIR"
: > "$LOG_FILE"

/opt/venvs/worker/bin/uvicorn serverless.backend:app \
  --host 127.0.0.1 \
  --port "$MODEL_PORT" \
  >>"$LOG_FILE" 2>&1 &

BACKEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

for _ in $(seq 1 90); do
  if curl -fsS "http://127.0.0.1:${MODEL_PORT}/health" >/dev/null; then
    echo "MORPHLY_BACKEND_READY"
    exec /opt/venvs/worker/bin/python /opt/morphly/serverless/worker.py
  fi
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "Backend exited before becoming healthy."
    cat "$LOG_FILE"
    exit 1
  fi
  sleep 1
done

echo "Backend health check timed out."
cat "$LOG_FILE"
exit 1
