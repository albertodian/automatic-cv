#!/bin/bash

# Start API Server with Auto-Reload (Development Mode)
# This script starts the FastAPI server with hot-reload enabled
# so you don't need to restart after making code changes

echo "🚀 Starting Automatic CV Generator API Server..."
echo "📝 Running in DEVELOPMENT mode with auto-reload enabled"
echo ""
echo "API will be available at:"
echo "  • http://localhost:8000"
echo "  • http://localhost:8000/docs (Swagger UI)"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Change to the app directory
cd "$(dirname "$0")/app"

# Start uvicorn with reload enabled
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
