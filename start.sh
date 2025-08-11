#!/bin/bash

# Startup script for Render deployment
echo "🚀 Starting LLM-Based Multi-Database Chatbot System..."

# Set environment variables
export TRANSFORMERS_OFFLINE=1
export HF_HUB_DISABLE_TELEMETRY=1
export PYTHONUNBUFFERED=1

# Print environment info
echo "📍 Environment variables:"
echo "  - TRANSFORMERS_OFFLINE: $TRANSFORMERS_OFFLINE"
echo "  - HF_HUB_DISABLE_TELEMETRY: $HF_HUB_DISABLE_TELEMETRY"
echo "  - PYTHONUNBUFFERED: $PYTHONUNBUFFERED"
echo "  - OPENAI_API_KEY: ${OPENAI_API_KEY:+set}"
echo "  - PORT: ${PORT:-8000}"

# Check if required files exist
echo "🔍 Checking required files..."
if [ -f "main.py" ]; then
    echo "✅ main.py exists"
else
    echo "❌ main.py not found"
    exit 1
fi

if [ -d "data" ]; then
    echo "✅ data directory exists"
else
    echo "❌ data directory not found"
    exit 1
fi

if [ -d "models" ]; then
    echo "✅ models directory exists"
else
    echo "❌ models directory not found"
    exit 1
fi

if [ -d "csv" ]; then
    echo "✅ csv directory exists"
else
    echo "❌ csv directory not found"
    exit 1
fi

# Check if uvicorn is available
echo "🔍 Checking uvicorn availability..."
if command -v uvicorn &> /dev/null; then
    echo "✅ uvicorn found in PATH"
    UVICORN_CMD="uvicorn"
elif python -m uvicorn --help &> /dev/null; then
    echo "✅ uvicorn available via python -m"
    UVICORN_CMD="python -m uvicorn"
else
    echo "❌ uvicorn not found"
    echo "🔍 Available Python packages:"
    pip list | grep -i uvicorn || echo "No uvicorn found in pip list"
    exit 1
fi

# Start the application
echo "🚀 Starting uvicorn server with command: $UVICORN_CMD"
exec $UVICORN_CMD main:app --host 0.0.0.0 --port ${PORT:-8000}
