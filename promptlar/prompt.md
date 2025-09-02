✅ OTO-KEŞİF (Referans):
Backend: python main.py → 0.0.0.0:8000 (FastAPI)
Frontend: streamlit run app.py → 0.0.0.0:8500
SQLite: Proje kökü: ./ai_helper.db, ENV: DATABASE_URL="sqlite:///./ai_helper.db"
Health: GET /api/v1/auth/health → {"status":"healthy",...}
Bu bilgiler doğru. Şimdi Docker Compose ile publish etme planını anlatabilirsin! 🚀



ADIM 1) start.sh ekle (iki süreci birlikte)
────────────────────────────────
# path: docker/start.sh
#!/usr/bin/env bash
set -euo pipefail
: "${API_PORT:=8000}"
: "${WEB_PORT:=8500}"

# Backend (FastAPI)
python main.py &

# Frontend (Streamlit)
streamlit run app.py \
  --server.port "${WEB_PORT}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --browser.gatherUsageStats false &

wait -n


ADIM 2) Dockerfile oluştur
────────────────────────────────
# path: Dockerfile
FROM python:3.11-slim
WORKDIR /app

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Python bağımlılıkları
COPY requirements*.txt /app/
RUN pip install --no-cache-dir -r requirements.txt || true

# Uygulama kodu ve start script
COPY . /app
RUN chmod +x /app/docker/start.sh

EXPOSE 8000 8500
ENTRYPOINT ["bash", "/app/docker/start.sh"]

ADIM 3) docker-compose.yml ekle (compose kullanalım)
────────────────────────────────
# path: docker-compose.yml
services:
  ai-helperv2:
    container_name: ai-helperv2-container
    build: .
    env_file: .env
    environment:
      APP_ENV: "production"
      DEBUG_MODE: "false"
      LOG_LEVEL: "INFO"
      API_PORT: "8000"
      WEB_PORT: "8500"
      # Programı değiştirmeden DB yolunu volume'a yönlendiriyoruz:
      DATABASE_URL: "sqlite:////app/data/ai_helper.db"
      ALLOWED_ORIGINS: "https://yardimci.niluferyapayzeka.tr"
    ports:
      - "8000:8000"
      - "8500:8500"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:8000/api/v1/auth/health || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 5
      start_period: 20s


ADIM 4) SQLite’ı konteynere taşı (KOD DEĞİŞMEDEN)
────────────────────────────────
- Proje köküne “data/” klasörünü oluştur.
- Lokalde çalışan ai_helper.db dosyanı BURAYA kopyala:
  ./data/ai_helper.db
- Compose, bu dosyayı konteyner içinde /app/data/ai_helper.db olarak görecek.
- DATABASE_URL’ı compose içinde "sqlite:////app/data/ai_helper.db" yaptığımız için uygulama koduna DOKUNMUYORUZ.

ADIM 5) .env kontrolü (sadece ortam)
────────────────────────────────
- Var olan SMTP ve diğer ENV’leri aynen koru.
- APP_ENV=production, DEBUG kapalı.
- “magic link” kelimesi geçen hiçbir metni değiştirme; e-posta metinleri zaten doğru ifadeyi kullanıyor.


ADIM 6) Compose ile ayağa kaldır
────────────────────────────────
- docker compose komutlarını sen çalıştır (Cursor biliyor).
- İlk çalıştırmada ./data içindeki ai_helper.db kullanılarak konteyner açılmalı.
- Health: http://localhost:8000/api/v1/auth/health → 200

ADIM 7) Cloudflare (bilgi amaçlı)
────────────────────────────────
- Public Hostnames:
  yardimci.niluferyapayzeka.tr  →  *      → http://localhost:8500
  yardimci.niluferyapayzeka.tr  →  api/*  → http://localhost:8000
- Dışarıdan test:
  https://yardimci.niluferyapayzeka.tr/                    (Streamlit)
  https://yardimci.niluferyapayzeka.tr/api/v1/auth/health  (API)



ADIM 8) Basit doğrulama
────────────────────────────────
- Kullanıcılar ve sayaçlar: Arayüzde eski veriler görünüyor olmalı (db taşındıysa OK).
- “Yanıt Üret” akışı lokaldeki gibi çalışmalı.
- Kopyalama sonrası “Cevaplanan İstek” sayısı aynı mantıkla artmalı.
- Konteyner yeniden başlatıldığında veriler ./data volume’unda kalmalı.