# Automatic CV Generator - REST API Documentation

## Overview

The Automatic CV Generator API provides AI-powered CV optimization and generation services. It accepts job postings and generates tailored CVs using machine learning.

## Base URL

```
http://localhost:8000
```

For production: `https://your-domain.com`

## Authentication

Currently no authentication required. Add API keys for production deployment.

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check API status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-04T12:00:00",
  "service": "cv-generator-api"
}
```

---

### 2. Generate CV from Job URL

**POST** `/api/v1/cv/generate/url`

Generate an optimized CV from a job posting URL.

**Request Body:**
```json
{
  "job_url": "https://example.com/job-posting",
  "template": "tech",
  "skip_validation": false,
  "max_retries": 2
}
```

**Parameters:**
- `job_url` (required): URL of the job posting
- `template` (optional): Template style - `"tech"`, `"business"`, or `"modern"` (default: `"tech"`)
- `skip_validation` (optional): Skip CV validation (default: `false`)
- `max_retries` (optional): Max validation retry attempts, 0-5 (default: `2`)

**Response:**
- Content-Type: `application/pdf`
- Returns the generated CV as a PDF file

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/cv/generate/url" \
  -H "Content-Type: application/json" \
  -d '{
    "job_url": "https://www.linkedin.com/jobs/view/123456",
    "template": "modern"
  }' \
  --output my_cv.pdf
```

---

### 3. Generate CV from Job Text

**POST** `/api/v1/cv/generate/text`

Generate an optimized CV from raw job description text.

**Request Body:**
```json
{
  "job_text": "We are looking for a Senior Software Engineer...",
  "template": "business",
  "skip_validation": false,
  "max_retries": 2
}
```

**Parameters:**
- `job_text` (required): Raw job description text
- `template` (optional): Template style (default: `"tech"`)
- `skip_validation` (optional): Skip CV validation (default: `false`)
- `max_retries` (optional): Max validation retry attempts (default: `2`)

**Response:**
- Content-Type: `application/pdf`
- Returns the generated CV as a PDF file

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/cv/generate/text",
    json={
        "job_text": "Looking for Python developer with FastAPI experience...",
        "template": "tech"
    }
)

with open("generated_cv.pdf", "wb") as f:
    f.write(response.content)
```

---

### 4. Parse Resume PDF

**POST** `/api/v1/cv/parse`

Extract structured data from an existing PDF resume.

**Request:**
- Content-Type: `multipart/form-data`
- Field: `file` (PDF file)

**Response:**
```json
{
  "status": "success",
  "message": "Resume parsed successfully",
  "job_id": "20251004_120000_abc123",
  "data": {
    "personal_info": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "location": "San Francisco, CA",
      "linkedin": "linkedin.com/in/johndoe",
      "github": "github.com/johndoe"
    },
    "summary": "Experienced software engineer...",
    "education": [...],
    "experience": [...],
    "projects": [...],
    "skills": {...}
  }
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/cv/parse" \
  -F "file=@my_resume.pdf"
```

---

### 5. Extract Job Information

**POST** `/api/v1/job/extract`

Extract structured information from a job posting.

**Request Body (Option 1 - URL):**
```json
{
  "job_url": "https://example.com/job-posting"
}
```

**Request Body (Option 2 - Text):**
```json
{
  "job_text": "We are looking for..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Job information extracted successfully",
  "job_id": "20251004_120000_xyz789",
  "data": {
    "title": "Senior Software Engineer",
    "company": "Tech Corp",
    "location": "Remote",
    "summary": "Tech Corp is seeking...",
    "requirements": [
      "5+ years Python experience",
      "Strong FastAPI knowledge"
    ],
    "responsibilities": [
      "Design and implement APIs",
      "Lead technical projects"
    ],
    "keywords": [
      "API",
      "FastAPI",
      "Python",
      "REST"
    ]
  }
}
```

---

### 6. Generate CV with Custom Profile

**POST** `/api/v1/cv/generate/custom`

Generate CV using custom profile data instead of the default profile.

**Request Body:**
```json
{
  "profile": {
    "personal_info": {
      "name": "Jane Doe",
      "email": "jane@example.com",
      "phone": "+1234567890",
      "location": "New York, NY",
      "linkedin": "linkedin.com/in/janedoe",
      "github": "github.com/janedoe"
    },
    "summary": "Passionate developer...",
    "education": [
      {
        "degree": "B.S. Computer Science",
        "institution": "MIT",
        "graduation_date": "2020",
        "gpa": "3.9"
      }
    ],
    "experience": [
      {
        "title": "Software Engineer",
        "company": "Tech Company",
        "start_date": "Jan 2020",
        "end_date": "Present",
        "descrition_list": [
          "Built scalable APIs",
          "Improved performance by 40%"
        ]
      }
    ],
    "projects": [
      {
        "name": "AI Chatbot",
        "description": "Built chatbot using GPT-4",
        "technologies": ["Python", "OpenAI", "FastAPI"],
        "link": "github.com/jane/chatbot"
      }
    ],
    "skills": {
      "programming_languages": ["Python", "JavaScript"],
      "frameworks": ["FastAPI", "React"],
      "tools": ["Docker", "Git"],
      "soft_skills": ["Leadership", "Communication"]
    }
  },
  "job_text": "Looking for Senior Developer...",
  "template": "modern",
  "skip_validation": false,
  "max_retries": 2
}
```

**Response:**
- Content-Type: `application/pdf`
- Returns the generated CV as a PDF file

---

## Template Styles

### 1. **tech** (Default)
- Clean, minimalist design
- Ideal for software engineering roles
- Focuses on technical skills and projects

### 2. **business**
- Modern with gradient elements
- Two-column layout
- Ideal for business/corporate roles
- Professional card-based design

### 3. **modern**
- Timeline-style layout
- Blue accent colors
- Single-column compact design
- Perfect for creative/modern companies

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Only PDF files are supported"
}
```

### 404 Not Found
```json
{
  "status": "error",
  "message": "Endpoint not found",
  "path": "/api/v1/invalid"
}
```

### 500 Internal Server Error
```json
{
  "detail": "CV generation failed: [error details]"
}
```

---

## Rate Limiting

Currently no rate limiting. Implement for production:
- Recommended: 10 requests per minute per IP
- Use Redis or similar for distributed rate limiting

---

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
cd app
python app.py

# Or use uvicorn directly
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment

#### Option 1: Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t cv-generator-api .
docker run -p 8000:8000 -e REPLICATE_API_TOKEN=your_token cv-generator-api
```

#### Option 2: Traditional Server (systemd)

```ini
[Unit]
Description=CV Generator API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/cv-generator
Environment="REPLICATE_API_TOKEN=your_token"
ExecStart=/usr/bin/uvicorn app.app:app --host 0.0.0.0 --port 8000 --workers 4

[Install]
WantedBy=multi-user.target
```

#### Option 3: Cloud Platforms

**Heroku:**
```bash
echo "web: uvicorn app.app:app --host 0.0.0.0 --port \$PORT" > Procfile
git push heroku main
```

**Railway/Render:**
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.app:app --host 0.0.0.0 --port $PORT`

**AWS Lambda (using Mangum):**
```python
from mangum import Mangum
handler = Mangum(app)
```

---

## Environment Variables

```bash
# Required
REPLICATE_API_TOKEN=your_replicate_api_token

# Optional
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://your-frontend.com
```

---

## Frontend Integration Examples

### JavaScript/Fetch

```javascript
// Generate CV from URL
async function generateCV(jobUrl) {
  const response = await fetch('http://localhost:8000/api/v1/cv/generate/url', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      job_url: jobUrl,
      template: 'modern'
    })
  });
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'my_cv.pdf';
  a.click();
}

// Parse resume
async function parseResume(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/api/v1/cv/parse', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  console.log(result.data);
}
```

### Python/Requests

```python
import requests

# Generate CV
def generate_cv(job_url: str, template: str = "tech"):
    response = requests.post(
        "http://localhost:8000/api/v1/cv/generate/url",
        json={"job_url": job_url, "template": template}
    )
    
    with open("generated_cv.pdf", "wb") as f:
        f.write(response.content)
    
    return "generated_cv.pdf"

# Parse resume
def parse_resume(pdf_path: str):
    with open(pdf_path, "rb") as f:
        files = {"file": f}
        response = requests.post(
            "http://localhost:8000/api/v1/cv/parse",
            files=files
        )
    
    return response.json()["data"]
```

---

## API Clients

### Python Client Example

```python
# cv_api_client.py
import requests
from typing import Optional

class CVGeneratorClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def generate_cv_from_url(
        self, 
        job_url: str, 
        template: str = "tech",
        output_path: str = "cv.pdf"
    ) -> str:
        """Generate CV from job URL"""
        response = requests.post(
            f"{self.base_url}/api/v1/cv/generate/url",
            json={"job_url": job_url, "template": template}
        )
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        return output_path
    
    def parse_resume(self, pdf_path: str) -> dict:
        """Parse existing resume"""
        with open(pdf_path, "rb") as f:
            response = requests.post(
                f"{self.base_url}/api/v1/cv/parse",
                files={"file": f}
            )
        response.raise_for_status()
        return response.json()["data"]

# Usage
client = CVGeneratorClient()
cv_path = client.generate_cv_from_url(
    "https://linkedin.com/jobs/view/123",
    template="modern"
)
print(f"CV generated: {cv_path}")
```

---

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test CV generation
curl -X POST "http://localhost:8000/api/v1/cv/generate/text" \
  -H "Content-Type: application/json" \
  -d '{"job_text": "Python developer needed", "template": "tech"}' \
  --output test_cv.pdf

# Test resume parsing
curl -X POST "http://localhost:8000/api/v1/cv/parse" \
  -F "file=@sample_resume.pdf" | jq .
```

---

## Monitoring & Logging

The API logs all operations with job IDs for tracking:

```
[20251004_120000_abc123] Starting CV generation from URL: https://...
[20251004_120000_abc123] Fetching job description...
[20251004_120000_abc123] Extracting job information...
[20251004_120000_abc123] Loading candidate profile...
[20251004_120000_abc123] Generating optimized CV...
[20251004_120000_abc123] Rendering PDF...
[20251004_120000_abc123] CV generation complete!
```

Implement monitoring with:
- Application logs → CloudWatch/Datadog
- Error tracking → Sentry
- Performance monitoring → New Relic/AppDynamics

---

## Security Considerations

For production deployment:

1. **API Authentication**: Add JWT or API key authentication
2. **Rate Limiting**: Prevent abuse (use slowapi or nginx)
3. **Input Validation**: Already implemented via Pydantic models
4. **File Upload Limits**: Set max file size (currently unlimited)
5. **CORS**: Configure allowed origins properly
6. **HTTPS**: Always use TLS in production
7. **Environment Variables**: Never commit API tokens

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/albertodian/automatic-cv/issues
- Email: support@example.com

## License

[Your License Here]
