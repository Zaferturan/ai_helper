#!/bin/bash

# Backend'i arka planda başlat
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &

# Nginx'i başlat
nginx -g "daemon off;"
