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
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# Frontend dosyalarını Nginx'e kopyala
COPY frontend/ /usr/share/nginx/html/

# Frontend URL'lerini localhost'a çevir
RUN sed -i 's|https://yardimci.niluferyapayzeka.tr/api/v1|http://localhost:8000/api/v1|g' /usr/share/nginx/html/app.js && \
    sed -i 's|https://yardimci.niluferyapayzeka.tr|http://localhost:8500|g' /usr/share/nginx/html/app.js

# Nginx konfigürasyonu
COPY nginx.conf /etc/nginx/sites-available/default

# Port'ları aç
EXPOSE 8000 80

# Volume'ları mount et
VOLUME ["/app/data", "/app/logs"]

# Başlatma scripti
COPY start.sh .
RUN chmod +x start.sh

# Uygulama başlatma komutu
CMD ["./start.sh"]