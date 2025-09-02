# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
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

# Veritabanını doğru konuma kopyala
RUN cp /app/data/ai_helper.db /app/ai_helper.db

# Expose both ports
EXPOSE 8000 8500

# Set the startup script as entrypoint
ENTRYPOINT ["bash", "/app/docker/start.sh"] 