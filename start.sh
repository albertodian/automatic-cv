#!/bin/bash
cd /app/app
exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}
