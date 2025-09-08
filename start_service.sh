#!/bin/bash

# AI Helper Systemd Service Start Script
# Bu script hem backend hem frontend'i başlatır

cd /opt/ai-helper

# Virtual environment'ı aktifleştir
source venv/bin/activate

# Backend'i başlat
echo "🚀 Backend başlatılıyor..."
python main.py &

# Backend'in başlamasını bekle
sleep 5

# Frontend'i başlat
echo "🌐 Frontend başlatılıyor..."
streamlit run app.py --server.port 8500 --server.address 0.0.0.0 &

# Sonsuz döngüde bekle
while true; do
    sleep 10
done
