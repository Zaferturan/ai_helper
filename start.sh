#!/bin/bash

# .env dosyasını yükle (secrets live in volume, never baked into image)
set -a
source /app/data/.env
set +a

# Uvicorn: loopback only — nginx on :80 is the sole public entry
python -m uvicorn main:app --host 127.0.0.1 --port 8000 &

# Nginx'i başlat
nginx -g "daemon off;"
