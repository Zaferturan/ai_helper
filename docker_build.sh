#!/bin/bash
# Yeni image build komutu

echo "🔨 Building Docker image..."
docker build -t ai_helperv2 .

if [ $? -eq 0 ]; then
    echo "✅ Image built successfully!"
    
    # Container çalışıyorsa dosyaları güncelle
    if docker ps | grep -q ai_helper_container_v2; then
        echo "📦 Updating files in running container..."
        
        # Frontend dosyalarını container'a kopyala
        docker cp frontend/index.html ai_helper_container_v2:/usr/share/nginx/html/ 2>/dev/null
        docker cp frontend/app.js ai_helper_container_v2:/usr/share/nginx/html/ 2>/dev/null
        docker cp frontend/style.css ai_helper_container_v2:/usr/share/nginx/html/ 2>/dev/null
        
        echo "✅ Files updated in container!"
        echo "🔄 Restarting container..."
        docker restart ai_helper_container_v2
        
        echo "✅ Container restarted!"
    else
        echo "ℹ️  Container not running. Start it with ./docker_run_new.sh"
    fi
else
    echo "❌ Build failed!"
    exit 1
fi
