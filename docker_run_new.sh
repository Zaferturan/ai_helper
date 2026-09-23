#!/bin/bash
# Cloudflare: all hops → localhost:8500 (nginx proxies /api/ internally)
# Restart policy: always

docker run -d \
  --name ai_helper_container_v2 \
  --restart=always \
  --network monitoring \
  -p 8500:80 \
  -v ai_helper_data_v2:/app/data \
  -v ai_helper_logs_v2:/app/logs \
  ai_helperv2
