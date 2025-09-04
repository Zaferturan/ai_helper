#!/usr/bin/env bash
set -euo pipefail
: "${API_PORT:=8000}"
: "${WEB_PORT:=8500}"

# Venv'i aktifleştir
source /app/venv/bin/activate

# Backend (FastAPI)
python main.py &

# Frontend (Streamlit)
streamlit run app.py \
  --server.port "${WEB_PORT}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --browser.gatherUsageStats false &

wait -n

