# API Quick Reference Card

## 🚀 Starting the API

```bash
# Quick start
./start_api.sh

# Manual start
uvicorn app.app:app --host 0.0.0.0 --port 8000 --reload

# Docker
docker-compose up -d
```

## 📍 Base Endpoints

| URL | Description |
|-----|-------------|
| `http://localhost:8000` | API root info |
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000/docs` | Interactive API docs |

---

## 🔥 Most Used Endpoints

### 1️⃣ Generate CV from URL

**POST** `/api/v1/cv/generate/url`

```bash
curl -X POST "http://localhost:8000/api/v1/cv/generate/url" \
  -H "Content-Type: application/json" \
  -d '{"job_url": "https://...", "template": "modern"}' \
  -o cv.pdf
```

**Python:**
```python
import requests
r = requests.post("http://localhost:8000/api/v1/cv/generate/url",
                  json={"job_url": "https://...", "template": "modern"})
with open("cv.pdf", "wb") as f: f.write(r.content)
```

---

### 2️⃣ Generate CV from Text

**POST** `/api/v1/cv/generate/text`

```bash
curl -X POST "http://localhost:8000/api/v1/cv/generate/text" \
  -H "Content-Type: application/json" \
  -d '{"job_text": "Looking for Python dev...", "template": "tech"}' \
  -o cv.pdf
```

**Python:**
```python
r = requests.post("http://localhost:8000/api/v1/cv/generate/text",
                  json={"job_text": "...", "template": "tech"})
with open("cv.pdf", "wb") as f: f.write(r.content)
```

---

### 3️⃣ Parse Resume PDF

**POST** `/api/v1/cv/parse`

```bash
curl -X POST "http://localhost:8000/api/v1/cv/parse" \
  -F "file=@resume.pdf"
```

**Python:**
```python
files = {"file": open("resume.pdf", "rb")}
r = requests.post("http://localhost:8000/api/v1/cv/parse", files=files)
data = r.json()["data"]
```

---

### 4️⃣ Extract Job Info

**POST** `/api/v1/job/extract`

```bash
# From URL
curl -X POST "http://localhost:8000/api/v1/job/extract" \
  -H "Content-Type: application/json" \
  -d '{"job_url": "https://..."}'

# From text
curl -X POST "http://localhost:8000/api/v1/job/extract" \
  -H "Content-Type: application/json" \
  -d '{"job_text": "..."}'
```

---

## 🎨 Template Options

| Value | Style | Best For |
|-------|-------|----------|
| `tech` | Clean, minimal | Software engineering |
| `business` | Professional, gradient | Corporate roles |
| `modern` | Timeline, creative | Modern companies |

---

## 📦 Request Body Examples

### Full CV Generation Request
```json
{
  "job_url": "https://linkedin.com/jobs/view/123",
  "template": "modern",
  "skip_validation": false,
  "max_retries": 2
}
```

### Custom Profile Request
```json
{
  "profile": {
    "personal_info": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "location": "San Francisco, CA"
    },
    "summary": "Experienced developer...",
    "education": [...],
    "experience": [...],
    "projects": [...],
    "skills": {...}
  },
  "job_text": "Looking for...",
  "template": "tech"
}
```

---

## 🔍 Response Examples

### Success (CV Generation)
- Content-Type: `application/pdf`
- Binary PDF file

### Success (Parse/Extract)
```json
{
  "status": "success",
  "message": "Resume parsed successfully",
  "job_id": "20251004_120000_abc123",
  "data": {
    "personal_info": {...},
    "summary": "...",
    "education": [...],
    "experience": [...],
    "projects": [...],
    "skills": {...}
  }
}
```

### Error
```json
{
  "detail": "Error message here"
}
```

---

## ⚡ JavaScript Quick Start

```javascript
// Generate CV
async function generateCV(jobUrl, template = 'modern') {
  const response = await fetch('http://localhost:8000/api/v1/cv/generate/url', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_url: jobUrl, template })
  });
  
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'cv.pdf';
  a.click();
}

// Parse Resume
async function parseResume(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/api/v1/cv/parse', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
}
```

---

## 🐍 Python Complete Client

```python
import requests

class CVGeneratorClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def generate_cv(self, job_url, template="tech", output="cv.pdf"):
        r = requests.post(f"{self.base_url}/api/v1/cv/generate/url",
                         json={"job_url": job_url, "template": template})
        r.raise_for_status()
        with open(output, "wb") as f:
            f.write(r.content)
        return output
    
    def parse_resume(self, pdf_path):
        with open(pdf_path, "rb") as f:
            r = requests.post(f"{self.base_url}/api/v1/cv/parse",
                            files={"file": f})
        r.raise_for_status()
        return r.json()["data"]

# Usage
client = CVGeneratorClient()
client.generate_cv("https://linkedin.com/jobs/view/123", "modern")
```

---

## 🔒 Security (Production)

### Add API Key Authentication

```python
# In app.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

@app.post("/api/v1/cv/generate/url", dependencies=[Security(verify_api_key)])
async def generate_cv(...):
    ...
```

**Client usage:**
```python
headers = {"X-API-Key": "your-secret-key"}
requests.post(url, json=data, headers=headers)
```

---

## 🐳 Docker Commands

```bash
# Build
docker build -t cv-api .

# Run
docker run -d -p 8000:8000 \
  -e REPLICATE_API_TOKEN=your_token \
  cv-api

# Logs
docker logs -f container_id

# Stop
docker stop container_id
```

---

## 📊 Monitoring

```python
# Add request logging
import logging
logging.basicConfig(level=logging.INFO)

@app.middleware("http")
async def log_requests(request, call_next):
    logging.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logging.info(f"Status: {response.status_code}")
    return response
```

---

## 🚨 Common Issues

| Problem | Solution |
|---------|----------|
| Port 8000 in use | `lsof -i :8000` then `kill -9 <PID>` |
| CORS errors | Add origin to `allow_origins` in app.py |
| Large file timeout | Increase `proxy_read_timeout` in nginx |
| Module not found | `pip install -r requirements.txt` |
| WeasyPrint error | `apt install libpango-1.0-0` |

---

## 📚 Documentation Links

- Full API Docs: `http://localhost:8000/docs`
- README: `README.md`
- API Reference: `API_DOCUMENTATION.md`
- Deployment Guide: `DEPLOYMENT.md`

---

## 💡 Pro Tips

1. **Batch Processing**: Use async requests for multiple CVs
2. **Caching**: Cache job extraction results to save API calls
3. **Error Handling**: Always wrap requests in try-catch
4. **Rate Limiting**: Implement rate limiting for production
5. **Monitoring**: Use health checks for uptime monitoring

---

## 🎯 Example Workflows

### Workflow 1: Job Application Bot
```python
# 1. Extract job info
job_info = client.extract_job_info(job_url)

# 2. Generate optimized CV
cv_path = client.generate_cv(job_url, template="modern")

# 3. Auto-submit application (your code)
submit_application(cv_path, job_info)
```

### Workflow 2: CV Update Service
```python
# 1. Parse existing CV
current_cv = client.parse_resume("old_cv.pdf")

# 2. Update with new job
new_cv = client.generate_cv_custom(current_cv, new_job_text)

# 3. Send notification
send_email(new_cv)
```

---

**Last Updated**: October 2025  
**API Version**: 1.0.0  
**Author**: Alberto Dian
