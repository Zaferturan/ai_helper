# 🤖 AI Helper Systemctl Service Setup Guide

## 📋 Özet
Bu dosya, AI Helper uygulamasını systemctl servisi olarak çalıştırmak için gerekli tüm adımları içerir.

## 🔧 Kurulum Adımları

### 1. Symbolic Link Oluştur
```bash
sudo ln -sf "/media/yapayzeka/depo/cursor projects/ai_helper" /opt/ai-helper
```

### 2. Service Dosyalarını Oluştur

#### `ai-helper.service`
```ini
[Unit]
Description=AI Helper Application
After=network.target
Wants=network.target

[Service]
Type=simple
User=yapayzeka
Group=yapayzeka
WorkingDirectory=/opt/ai-helper
Environment=PATH=/opt/ai-helper/venv/bin
ExecStart=/opt/ai-helper/start_service.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### `start_service.sh`
```bash
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
```

#### `manage_service.sh`
```bash
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
```

### 3. Dosyaları Çalıştırılabilir Yap
```bash
chmod +x start_service.sh
chmod +x manage_service.sh
```

### 4. E-posta Link Sorununu Düzelt
```bash
# .env dosyasındaki çakışan satırı sil
sed -i '/^PRODUCTION_URL=http:\/\/localhost:8500$/d' .env

# Kontrol et
cat .env | grep PRODUCTION_URL
# Çıktı: PRODUCTION_URL=https://yardimci.niluferyapayzeka.tr
```

### 5. Servisi Kur ve Başlat
```bash
./manage_service.sh install
./manage_service.sh start
```

## 🎯 Kullanım Komutları

### Servis Yönetimi
```bash
# Kurulum
./manage_service.sh install

# Başlatma
./manage_service.sh start

# Durdurma
./manage_service.sh stop

# Yeniden başlatma
./manage_service.sh restart

# Durum kontrolü
./manage_service.sh status

# Logları görme
./manage_service.sh logs

# Kaldırma
./manage_service.sh uninstall
```

### Doğrudan Systemctl
```bash
sudo systemctl start ai-helper
sudo systemctl stop ai-helper
sudo systemctl restart ai-helper
sudo systemctl status ai-helper
sudo journalctl -u ai-helper -f
```

## ✅ Test Etme

### Health Check
```bash
curl -s http://localhost:8000/api/v1/auth/health
# Beklenen: {"status":"healthy","service":"authentication"}
```

### Frontend Test
```bash
curl -s http://localhost:8500
# Beklenen: HTML içeriği
```

### Production URL
```bash
google-chrome https://yardimci.niluferyapayzeka.tr/
```

## 🔍 Sorun Giderme

### Servis Başlamıyorsa
```bash
# Logları kontrol et
sudo journalctl -u ai-helper -n 50

# Servis durumunu kontrol et
sudo systemctl status ai-helper

# Path kontrolü
ls -la /opt/ai-helper
```

### E-posta Linkleri Hala Localhost Gösteriyorsa
```bash
# .env dosyasını kontrol et
cat .env | grep PRODUCTION_URL

# Servisi yeniden başlat
./manage_service.sh restart
```

## 📊 Servis Özellikleri

- ✅ Otomatik yeniden başlatma
- ✅ Sistem başlangıcında otomatik başlatma
- ✅ Detaylı loglar
- ✅ Bellek kullanımı: ~110MB
- ✅ Backend: localhost:8000
- ✅ Frontend: localhost:8500
- ✅ Production: https://yardimci.niluferyapayzeka.tr/

## 🎉 Tamamlandı!

Servis başarıyla kurulduğunda:
- Backend ve frontend otomatik çalışır
- Sistem yeniden başlatıldığında otomatik başlar
- E-posta linkleri doğru production URL'ini kullanır
- Loglar systemd journal'da tutulur

---
*Son güncelleme: 2025-09-04*


