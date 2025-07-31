#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Start backend API in background
echo "Starting backend API on port 8000..."
python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start Streamlit
echo "Starting Streamlit on port 8500..."
streamlit run app.py --server.port=8500 --server.address=0.0.0.0

# If Streamlit exits, kill backend
kill $BACKEND_PID 