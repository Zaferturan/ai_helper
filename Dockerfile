FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Copy and set permissions for startup script
COPY start_services.sh .
RUN chmod +x start_services.sh

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose both Streamlit and API ports
EXPOSE 8500 8000

# Health check for both services
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8500/_stcore/health && curl -f http://localhost:8000/ || exit 1

# Start both services using a startup script
CMD ["./start_services.sh"] 