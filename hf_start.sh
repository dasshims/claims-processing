#!/usr/bin/env bash
set -euo pipefail

cd /app/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &

cd /app/web
API_BASE_URL="http://127.0.0.1:8000" npm run start -- --hostname 0.0.0.0 --port "${PORT:-7860}"
