# Deployment Guide - Automatic CV Generator API

This guide covers various deployment options for the CV Generator API.

---

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Platform Deployment](#cloud-platform-deployment)
4. [Traditional Server Deployment](#traditional-server-deployment)
5. [Production Best Practices](#production-best-practices)

---

## Local Development

### Prerequisites

- Python 3.10 or higher
- Tesseract OCR (optional, for scanned PDFs)
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/albertodian/automatic-cv.git
cd automatic-cv

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your REPLICATE_API_TOKEN

# Run the API
cd app
python app.py
```

The API will be available at `http://localhost:8000`

### Development Mode

```bash
# With auto-reload
uvicorn app.app:app --reload --host 0.0.0.0 --port 8000

# View API documentation
# Open browser to http://localhost:8000/docs
```

---

## Docker Deployment

### Quick Start

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f cv-api

# Stop
docker-compose down
```

### Manual Docker Build

```bash
# Build image
docker build -t cv-generator-api .

# Run container
docker run -d \
  --name cv-api \
  -p 8000:8000 \
  -e REPLICATE_API_TOKEN=your_token \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/output:/app/output \
  cv-generator-api

# Check logs
docker logs -f cv-api

# Stop container
docker stop cv-api
docker rm cv-api
```

### Docker with Nginx (Production)

```bash
# Start full stack (API + Nginx)
docker-compose up -d

# The API is now available at:
# - HTTP: http://localhost (proxied through Nginx)
# - Direct: http://localhost:8000

# Configure SSL certificates
mkdir ssl
# Copy your cert.pem and key.pem to ssl/
```

---

## Cloud Platform Deployment

### 1. Heroku

```bash
# Prerequisites: Heroku CLI installed

# Login to Heroku
heroku login

# Create app
heroku create your-cv-generator-api

# Add buildpacks for system dependencies
heroku buildpacks:add --index 1 heroku/apt
echo "tesseract-ocr poppler-utils" > Aptfile
git add Aptfile

# Create Procfile
echo "web: uvicorn app.app:app --host 0.0.0.0 --port \$PORT" > Procfile

# Set environment variables
heroku config:set REPLICATE_API_TOKEN=your_token

# Deploy
git push heroku main

# Open app
heroku open

# View logs
heroku logs --tail
```

### 2. Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.app:app --host 0.0.0.0 --port $PORT`
5. Add environment variable: `REPLICATE_API_TOKEN`
6. Deploy!

### 3. Render

1. Go to [render.com](https://render.com)
2. New → Web Service
3. Connect your GitHub repository
4. Configure:
   - Name: `cv-generator-api`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.app:app --host 0.0.0.0 --port $PORT`
5. Add environment variable: `REPLICATE_API_TOKEN`
6. Create Web Service

### 4. Google Cloud Run

```bash
# Prerequisites: gcloud CLI installed

# Build container
gcloud builds submit --tag gcr.io/PROJECT-ID/cv-generator-api

# Deploy
gcloud run deploy cv-generator-api \
  --image gcr.io/PROJECT-ID/cv-generator-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars REPLICATE_API_TOKEN=your_token \
  --memory 2Gi \
  --timeout 300s

# Get service URL
gcloud run services describe cv-generator-api --region us-central1
```

### 5. AWS Elastic Beanstalk

```bash
# Prerequisites: EB CLI installed

# Initialize
eb init -p python-3.10 cv-generator-api

# Create environment
eb create cv-api-env

# Set environment variables
eb setenv REPLICATE_API_TOKEN=your_token

# Deploy
eb deploy

# Open app
eb open

# View logs
eb logs
```

### 6. Azure App Service

```bash
# Prerequisites: Azure CLI installed

# Login
az login

# Create resource group
az group create --name cv-api-rg --location eastus

# Create app service plan
az appservice plan create \
  --name cv-api-plan \
  --resource-group cv-api-rg \
  --sku B1 \
  --is-linux

# Create web app
az webapp create \
  --resource-group cv-api-rg \
  --plan cv-api-plan \
  --name your-cv-api \
  --runtime "PYTHON:3.10"

# Configure environment variables
az webapp config appsettings set \
  --resource-group cv-api-rg \
  --name your-cv-api \
  --settings REPLICATE_API_TOKEN=your_token

# Deploy
az webapp up --name your-cv-api
```

---

## Traditional Server Deployment

### Ubuntu 20.04/22.04 (systemd)

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip \
  tesseract-ocr poppler-utils nginx

# 2. Create application user
sudo useradd -m -s /bin/bash cvapi
sudo su - cvapi

# 3. Clone and setup
git clone https://github.com/albertodian/automatic-cv.git
cd automatic-cv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env  # Add your REPLICATE_API_TOKEN

# 5. Create systemd service
sudo nano /etc/systemd/system/cv-api.service
```

**Service file content:**

```ini
[Unit]
Description=CV Generator API
After=network.target

[Service]
Type=simple
User=cvapi
WorkingDirectory=/home/cvapi/automatic-cv
Environment="PATH=/home/cvapi/automatic-cv/venv/bin"
EnvironmentFile=/home/cvapi/automatic-cv/.env
ExecStart=/home/cvapi/automatic-cv/venv/bin/uvicorn app.app:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 6. Start service
sudo systemctl daemon-reload
sudo systemctl enable cv-api
sudo systemctl start cv-api
sudo systemctl status cv-api

# 7. Configure Nginx
sudo nano /etc/nginx/sites-available/cv-api
```

**Nginx config:**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Large file upload
        client_max_body_size 10M;
        
        # Longer timeouts for CV generation
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/cv-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 8. Setup SSL with Certbot (optional but recommended)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Monitor logs

```bash
# Application logs
sudo journalctl -u cv-api -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## Production Best Practices

### 1. Security

#### API Authentication

Add authentication to protect your endpoints:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY = os.getenv("API_KEY", "your-secret-key")
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )

# Add to endpoints
@app.post("/api/v1/cv/generate/url", dependencies=[Depends(verify_api_key)])
async def generate_cv_from_url(...):
    ...
```

#### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/cv/generate/url")
@limiter.limit("5/minute")
async def generate_cv_from_url(...):
    ...
```

### 2. Monitoring

#### Health Checks

Already implemented at `/health` endpoint.

#### Application Monitoring

```python
# Add Sentry for error tracking
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

sentry_sdk.init(dsn="your-sentry-dsn")
app.add_middleware(SentryAsgiMiddleware)
```

#### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
```

### 3. Performance

#### Use Multiple Workers

```bash
# For production, use more workers
uvicorn app.app:app --workers 4 --host 0.0.0.0 --port 8000

# Or use Gunicorn with Uvicorn workers
gunicorn app.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Add Caching

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="cv-cache:")
```

### 4. Database for Job Tracking

For production, store job history:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Track generations
@app.post("/api/v1/cv/generate/url")
async def generate_cv_from_url(...):
    # Store in database
    db.add(JobRecord(
        job_id=job_id,
        job_url=request.job_url,
        template=request.template,
        created_at=datetime.now(),
        status="completed"
    ))
    db.commit()
```

### 5. Backups

```bash
# Backup important data daily
0 2 * * * tar -czf /backups/cv-data-$(date +\%Y\%m\%d).tar.gz /home/cvapi/automatic-cv/data
```

### 6. Environment-Specific Configs

```python
# config.py
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    environment: str = os.getenv("ENVIRONMENT", "development")
    replicate_token: str = os.getenv("REPLICATE_API_TOKEN")
    max_workers: int = int(os.getenv("MAX_WORKERS", "4"))
    
    class Config:
        case_sensitive = False

settings = Settings()
```

---

## Troubleshooting

### Common Issues

#### 1. Port already in use
```bash
# Find process using port 8000
lsof -i :8000
# Kill process
kill -9 <PID>
```

#### 2. Permission denied
```bash
# Make sure user has permissions
sudo chown -R cvapi:cvapi /home/cvapi/automatic-cv
```

#### 3. Module not found
```bash
# Ensure virtual environment is activated
source venv/bin/activate
# Reinstall dependencies
pip install -r requirements.txt
```

#### 4. WeasyPrint issues
```bash
# Install missing system dependencies
sudo apt install libpango-1.0-0 libpangoft2-1.0-0
```

---

## Scaling

### Horizontal Scaling

Use load balancer (Nginx/HAProxy) with multiple API instances:

```nginx
upstream cv_backend {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    server 127.0.0.1:8004;
}

server {
    location / {
        proxy_pass http://cv_backend;
    }
}
```

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cv-generator-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cv-api
  template:
    metadata:
      labels:
        app: cv-api
    spec:
      containers:
      - name: cv-api
        image: cv-generator-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: REPLICATE_API_TOKEN
          valueFrom:
            secretKeyRef:
              name: cv-api-secrets
              key: replicate-token
```

---

## Support

For deployment issues:
- Check logs: `docker logs cv-api` or `journalctl -u cv-api`
- GitHub Issues: https://github.com/albertodian/automatic-cv/issues
- Documentation: See API_DOCUMENTATION.md

## License

[Your License]
