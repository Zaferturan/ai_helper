# Docker Kurulum ve Yapılandırma Rehberi

## Docker Volumes

### 1. ai_helper_data Volume
- **Amaç:** Veritabanı ve konfigürasyon dosyalarını saklamak
- **İçerik:**
  - `ai_helper.db` - SQLite veritabanı
  - `.env` - Ortam değişkenleri dosyası
- **Oluşturma:** `docker volume create ai_helper_data`

### 2. ai_helper_logs Volume
- **Amaç:** Uygulama loglarını saklamak
- **İçerik:**
  - `backend.log` - FastAPI backend logları
  - Diğer uygulama logları
- **Oluşturma:** `docker volume create ai_helper_logs`

## Docker Image

### Image Adı: ai_helper_v3
- **Base Image:** python:3.11-slim
- **Portlar:** 8000 (backend), 80 (frontend)
- **Servisler:** Nginx (frontend), FastAPI (backend)

### Build Komutu:
```bash
docker build -t ai_helper_v3 .
```

## Docker Container

### Container Adı: ai_yardimci
- **Restart Policy:** always (bilgisayar her başladığında otomatik başlar)
- **Port Mapping:** 
  - Host 8500 → Container 80 (frontend)
  - Host 8000 → Container 8000 (backend)

### Çalıştırma Komutu:
```bash
docker run -d --name ai_yardimci --restart always \
  -p 8500:80 -p 8000:8000 \
  -v ai_helper_data:/app/data \
  -v ai_helper_logs:/app/logs \
  ai_helper_v3
```

## Önemli Dosyalar

### Dockerfile
- Frontend URL'lerini production'a çevirir
- Nginx konfigürasyonu
- Python bağımlılıkları

### nginx.conf
- Frontend dosyalarını serve eder
- API isteklerini backend'e proxy eder

### start.sh
- .env dosyasını yükler
- Backend'i arka planda başlatır
- Nginx'i başlatır

## Veri Transferi

### Mevcut Verileri Volume'a Aktarma:
```bash
# Database'i kopyala
sudo cp ai_helper.db /var/lib/docker/volumes/ai_helper_data/_data/

# .env dosyasını kopyala
sudo cp .env /var/lib/docker/volumes/ai_helper_data/_data/
```

## Konfigürasyon

### DATABASE_URL
- **Volume içinde:** `sqlite:///./data/ai_helper.db`
- **config.py'de:** Default değer volume path'ini kullanır

### Frontend URL'leri
- **Production:** `https://yardimci.niluferyapayzeka.tr`
- **Dockerfile'da:** Otomatik olarak production URL'lerine çevrilir

## Yönetim Komutları

### Container Yönetimi:
```bash
# Container'ı durdur
docker stop ai_yardimci

# Container'ı sil
docker rm ai_yardimci

# Container'ı yeniden başlat
docker restart ai_yardimci

# Container loglarını görüntüle
docker logs ai_yardimci
```

### Volume Yönetimi:
```bash
# Volume'ları listele
docker volume ls

# Volume içeriğini kontrol et
sudo ls -la /var/lib/docker/volumes/ai_helper_data/_data/

# Volume'u sil (DİKKAT: Veriler silinir!)
docker volume rm ai_helper_data
```

### Image Yönetimi:
```bash
# Image'ları listele
docker images

# Image'ı sil
docker rmi ai_helper_v3
```

## Sorun Giderme

### Port Çakışması:
```bash
# Port kullanımını kontrol et
lsof -i :8500
lsof -i :8000

# Process'i sonlandır
kill -9 <PID>
```

### Volume Mount Sorunları:
- Docker Desktop file sharing ayarlarını kontrol et
- `sudo cp` ile doğrudan host mount point'e kopyala

### Database Bağlantı Sorunları:
- `DATABASE_URL` environment variable'ını kontrol et
- Volume içindeki database dosyasının varlığını kontrol et

## Güncelleme Süreci

1. **Kod değişiklikleri yap**
2. **Container'ı durdur:** `docker stop ai_yardimci`
3. **Container'ı sil:** `docker rm ai_yardimci`
4. **Yeni image build et:** `docker build -t ai_helper_v3 .`
5. **Container'ı yeniden oluştur:** Yukarıdaki run komutu

## Production URL

- **Frontend:** https://yardimci.niluferyapayzeka.tr/
- **Backend API:** https://yardimci.niluferyapayzeka.tr/api/v1/
- **Cloudflare:** Routing yapılandırması aktif
