#!/usr/bin/env bash
set -euo pipefail

cd /app/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &

cd /app/frontend
export API_BASE="http://127.0.0.1:8000"
python -m streamlit run app.py \
  --server.address 0.0.0.0 \
  --server.port "${PORT:-7860}" \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false
