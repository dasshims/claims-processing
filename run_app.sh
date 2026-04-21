#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
WEB_DIR="$ROOT_DIR/web"

if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

if ! "$PYTHON_BIN" -c "import fastapi, uvicorn" >/dev/null 2>&1; then
  echo "Missing backend dependencies for $PYTHON_BIN."
  echo "Install them with:"
  echo "  $PYTHON_BIN -m pip install -r $ROOT_DIR/requirements.txt"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required to run the Next.js frontend."
  exit 1
fi

shutdown() {
  echo "\nStopping services..."
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  wait || true
}
trap shutdown INT TERM EXIT

echo "Installing frontend dependencies (if needed)..."
(
  cd "$WEB_DIR"
  npm install --silent
)

echo "Starting backend on http://localhost:8000"
(
  cd "$BACKEND_DIR"
  "$PYTHON_BIN" -m uvicorn main:app --reload
) &
BACKEND_PID=$!

echo "Starting Next.js frontend on http://localhost:3000"
(
  cd "$WEB_DIR"
  API_BASE_URL="http://127.0.0.1:8000" npm run dev -- --hostname 0.0.0.0 --port 3000
) &
FRONTEND_PID=$!

echo "Both services started. Press Ctrl+C to stop."
wait
