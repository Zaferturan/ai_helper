FROM python:3.11-slim

# Sistem paketlerini güncelle ve gerekli paketleri yükle
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizinini ayarla
WORKDIR /app

# Python bağımlılıklarını kopyala ve yükle
# requirements.txt önce kopyalanıyor (layer cache için)
COPY requirements.txt .
# pip cache kullanılıyor (daha hızlı build)
RUN pip install -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# Frontend dosyalarını Nginx'e kopyala
COPY frontend/ /usr/share/nginx/html/

# Frontend URL'lerini production'a çevir (yardimci ve yardimci2)
RUN sed -i 's|http://localhost:8000/api/v1|https://yardimci.niluferyapayzeka.tr/api/v1|g' /usr/share/nginx/html/app.js && \
    sed -i 's|http://localhost:8500|https://yardimci.niluferyapayzeka.tr|g' /usr/share/nginx/html/app.js

# Nginx konfigürasyonu
COPY nginx.conf /etc/nginx/sites-available/default

# Port'ları aç
EXPOSE 12000 80

# Volume'ları mount et
VOLUME ["/app/data", "/app/logs"]

# Başlatma scripti
COPY start.sh .
RUN chmod +x start.sh

# Uygulama başlatma komutu
CMD ["./start.sh"]