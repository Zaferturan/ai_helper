# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose both ports
EXPOSE 8000 8500

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting AI Helper application..."\n\
echo "Starting backend on port 8000..."\n\
python main.py &\n\
BACKEND_PID=$!\n\
echo "Starting frontend on port 8500..."\n\
streamlit run app.py --server.port 8500 --server.address 0.0.0.0 &\n\
FRONTEND_PID=$!\n\
echo "Both services started. Backend PID: $BACKEND_PID, Frontend PID: $FRONTEND_PID"\n\
wait $BACKEND_PID $FRONTEND_PID\n\
' > /app/start.sh && chmod +x /app/start.sh

# Set the startup script as entrypoint
ENTRYPOINT ["/app/start.sh"] 