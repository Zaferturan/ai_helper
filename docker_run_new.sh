#!/bin/bash
# Yeni container için docker run komutu
# Portlar: 12000 (backend), 13000 (frontend)
# Restart policy: always

docker run -d \
  --name ai_helper_container_v2 \
  --restart=always \
  --network monitoring \
  -p 12000:12000 \
  -p 13000:80 \
  -v ai_helper_data_v2:/app/data \
  -v ai_helper_logs_v2:/app/logs \
  ai_helperv2

