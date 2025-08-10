#!/bin/bash

# Deployment script for LLM-Based Multi-Database Chatbot System
# This script sets up the offline RAG system for deployment

set -e  # Exit on any error

echo "🚀 Starting deployment setup for LLM-Based Multi-Database Chatbot System"
echo "=" * 60

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if required directories exist
if [ ! -d "csv" ]; then
    print_error "CSV directory not found. Please ensure you have the csv/ directory with patient data."
    exit 1
fi

if [ ! -d "pdf" ]; then
    print_error "PDF directory not found. Please ensure you have the pdf/ directory with healthcare documents."
    exit 1
fi

# Step 1: Download and vendor the model
print_status "Step 1: Downloading and vendoring the sentence-transformers model..."
if [ ! -d "models/all-MiniLM-L6-v2" ]; then
    python3 download_model.py
    if [ $? -ne 0 ]; then
        print_error "Model download failed!"
        exit 1
    fi
else
    print_warning "Model directory already exists. Skipping download."
fi

# Step 2: Create data directory structure
print_status "Step 2: Setting up data directory structure..."
mkdir -p data

# Step 3: Create database and FAISS index
print_status "Step 3: Creating database and FAISS index..."
python3 setup_railway.py
if [ $? -ne 0 ]; then
    print_error "Database/FAISS setup failed!"
    exit 1
fi

# Step 4: Verify the setup
print_status "Step 4: Verifying the setup..."

# Check if database exists
if [ ! -f "data/healthcare.db" ]; then
    print_error "Database file not found!"
    exit 1
fi

# Check if FAISS index exists
if [ ! -d "data/faiss_index_notice_privacy" ]; then
    print_error "FAISS index directory not found!"
    exit 1
fi

# Check if model files exist
if [ ! -f "models/all-MiniLM-L6-v2/pytorch_model.bin" ]; then
    print_error "Model files not found!"
    exit 1
fi

print_status "✅ All files verified successfully!"

# Step 5: Test the application
print_status "Step 5: Testing the application..."
echo "Starting the application for testing..."

# Set environment variables for offline operation
export TRANSFORMERS_OFFLINE=1
export HF_HUB_DISABLE_TELEMETRY=1

# Start the application in background
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
APP_PID=$!

# Wait for the app to start
sleep 10

# Test health endpoint
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "✅ Application started successfully!"
else
    print_error "❌ Application failed to start!"
    kill $APP_PID 2>/dev/null || true
    exit 1
fi

# Stop the test application
kill $APP_PID 2>/dev/null || true

# Step 6: Build Docker image (optional)
if command -v docker &> /dev/null; then
    print_status "Step 6: Building Docker image..."
    docker build -t llm-multidb-chatbot .
    if [ $? -eq 0 ]; then
        print_status "✅ Docker image built successfully!"
        echo ""
        echo "🐳 To run the Docker container:"
        echo "   docker run -p 8000:8000 -e OPENAI_API_KEY=your_key_here llm-multidb-chatbot"
    else
        print_warning "⚠️ Docker build failed. You can still run the application directly."
    fi
else
    print_warning "⚠️ Docker not found. Skipping Docker build."
fi

echo ""
echo "🎉 Deployment setup completed successfully!"
echo ""
echo "📋 Summary:"
echo "   ✅ Model vendored: models/all-MiniLM-L6-v2/"
echo "   ✅ Database created: data/healthcare.db"
echo "   ✅ FAISS index created: data/faiss_index_notice_privacy/"
echo "   ✅ Application tested and working"
echo ""
echo "🚀 To run the application:"
echo "   export OPENAI_API_KEY=your_key_here"
echo "   python3 -m uvicorn main:app --host 0.0.0.0 --port 8000"
echo ""
echo "🌐 Access the application at: http://localhost:8000"
echo ""
echo "📝 For deployment to Railway/Render:"
echo "   1. Push this repository to GitHub"
echo "   2. Connect to Railway/Render"
echo "   3. Set OPENAI_API_KEY environment variable"
echo "   4. Deploy!"
