#!/bin/bash

# AI Helper Systemd Service Manager
# Bu script systemd servisini yönetir

SERVICE_NAME="ai-helper"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PROJECT_DIR="/opt/ai-helper"

echo "🤖 AI Helper Systemd Service Manager"
echo "======================================"

case "$1" in
    install)
        echo "📦 Servis dosyası kopyalanıyor..."
        sudo cp "${PROJECT_DIR}/ai-helper.service" "${SERVICE_FILE}"
        
        echo "🔄 Systemd yeniden yükleniyor..."
        sudo systemctl daemon-reload
        
        echo "✅ Servis etkinleştiriliyor..."
        sudo systemctl enable "${SERVICE_NAME}"
        
        echo "🎉 Servis başarıyla kuruldu!"
        echo "📋 Kullanım:"
        echo "   Başlatmak:   sudo systemctl start ${SERVICE_NAME}"
        echo "   Durdurmak:   sudo systemctl stop ${SERVICE_NAME}"
        echo "   Durum:       sudo systemctl status ${SERVICE_NAME}"
        echo "   Loglar:      sudo journalctl -u ${SERVICE_NAME} -f"
        ;;
        
    uninstall)
        echo "🛑 Servis durduruluyor..."
        sudo systemctl stop "${SERVICE_NAME}"
        
        echo "❌ Servis devre dışı bırakılıyor..."
        sudo systemctl disable "${SERVICE_NAME}"
        
        echo "🗑️ Servis dosyası siliniyor..."
        sudo rm -f "${SERVICE_FILE}"
        
        echo "🔄 Systemd yeniden yükleniyor..."
        sudo systemctl daemon-reload
        
        echo "✅ Servis başarıyla kaldırıldı!"
        ;;
        
    start)
        echo "🚀 Servis başlatılıyor..."
        sudo systemctl start "${SERVICE_NAME}"
        sudo systemctl status "${SERVICE_NAME}"
        ;;
        
    stop)
        echo "🛑 Servis durduruluyor..."
        sudo systemctl stop "${SERVICE_NAME}"
        sudo systemctl status "${SERVICE_NAME}"
        ;;
        
    restart)
        echo "🔄 Servis yeniden başlatılıyor..."
        sudo systemctl restart "${SERVICE_NAME}"
        sudo systemctl status "${SERVICE_NAME}"
        ;;
        
    status)
        echo "📊 Servis durumu:"
        sudo systemctl status "${SERVICE_NAME}"
        ;;
        
    logs)
        echo "📋 Servis logları:"
        sudo journalctl -u "${SERVICE_NAME}" -f
        ;;
        
    *)
        echo "❌ Geçersiz komut!"
        echo ""
        echo "📋 Kullanım:"
        echo "   $0 install     - Servisi kur ve etkinleştir"
        echo "   $0 uninstall   - Servisi kaldır"
        echo "   $0 start       - Servisi başlat"
        echo "   $0 stop        - Servisi durdur"
        echo "   $0 restart     - Servisi yeniden başlat"
        echo "   $0 status      - Servis durumunu göster"
        echo "   $0 logs        - Servis loglarını göster"
        echo ""
        echo "🌐 Uygulama URL'leri:"
        echo "   Backend:  http://localhost:8000"
        echo "   Frontend: http://localhost:8500"
        echo "   Production: https://yardimci.niluferyapayzeka.tr/"
        exit 1
        ;;
esac
