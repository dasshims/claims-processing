#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# Prefer project venv if present.
if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

if ! "$PYTHON_BIN" -c "import fastapi, streamlit, uvicorn" >/dev/null 2>&1; then
  echo "Missing dependencies for $PYTHON_BIN."
  echo "Install them with:"
  echo "  $PYTHON_BIN -m pip install -r $ROOT_DIR/requirements.txt"
  exit 1
fi

shutdown() {
  echo "\nStopping services..."
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  wait || true
}

trap shutdown INT TERM EXIT

echo "Starting backend on http://localhost:8000"
(
  cd "$BACKEND_DIR"
  "$PYTHON_BIN" -m uvicorn main:app --reload
) &
BACKEND_PID=$!

echo "Starting frontend on http://localhost:8501"
(
  cd "$FRONTEND_DIR"
  "$PYTHON_BIN" -m streamlit run app.py
) &
FRONTEND_PID=$!

echo "Both services started. Press Ctrl+C to stop."
wait
