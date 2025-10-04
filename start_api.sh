#!/bin/bash

# Startup script for CV Generator API

echo "==================================="
echo "CV Generator API - Startup Script"
echo "==================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please edit it and add your REPLICATE_API_TOKEN"
        exit 1
    else
        echo "❌ Error: .env.example not found!"
        exit 1
    fi
fi

# Check if REPLICATE_API_TOKEN is set
source .env
if [ -z "$REPLICATE_API_TOKEN" ]; then
    echo "❌ Error: REPLICATE_API_TOKEN not set in .env file"
    echo "Please edit .env and add your Replicate API token"
    exit 1
fi

# Create necessary directories
mkdir -p output/temp_api data

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "❌ Error: uvicorn not installed"
    echo "Run: pip install -r requirements.txt"
    exit 1
fi

echo "✅ Environment check passed"
echo ""
echo "Starting API server..."
echo "API will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "==================================="
echo ""

# Start the API
cd app
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
