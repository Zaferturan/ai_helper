# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Uygulama kodu ve venv'i kopyala
COPY . /app

# Venv'i aktifleştir ve bağımlılıkları yükle
RUN python -m venv /app/venv
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Start script'i çalıştırılabilir yap
RUN chmod +x /app/docker/start.sh

# Expose both ports
EXPOSE 8000 8500

# Set the startup script as entrypoint
ENTRYPOINT ["bash", "/app/docker/start.sh"] 