#!/bin/bash
# Yeni container için docker run komutu
# Cloudflare hops: api/static → :8000, frontend (*) → :8500
# Restart policy: always

docker run -d \
  --name ai_helper_container_v2 \
  --restart=always \
  --network monitoring \
  -p 8000:8000 \
  -p 8500:80 \
  -v ai_helper_data_v2:/app/data \
  -v ai_helper_logs_v2:/app/logs \
  ai_helperv2

