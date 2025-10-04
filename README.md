# Automatic CV Generator 🚀

An intelligent **AI-powered CV optimization and generation system** that automatically creates tailored, ATS-friendly CVs for any job posting. Available as both a **CLI tool** and a **REST API** for easy integration.

## ✨ Key Features

### 🤖 AI-Powered Optimization
- **Intelligent job parsing** – Extracts key requirements from any job posting URL or text
- **LLM-based CV optimization** – Uses GPT-4.1-mini (via Replicate API) to tailor your CV
- **Automatic keyword matching** – Ensures ATS compatibility with relevant keywords
- **Smart content validation** – Prevents hallucinations and enforces one-page limit

### 📄 Advanced CV Processing
- **PDF resume parsing** – Extract structured data from existing PDFs (with OCR support)
- **Multiple extraction methods** – pdfplumber, PyMuPDF, PyPDF2, and OCR fallback
- **Intelligent data structuring** – AI organizes unstructured resume text

### 🎨 Professional Templates
- **Tech Template** – Clean, minimalist design for software engineering roles
- **Business Template** – Modern gradient design with two-column layout
- **Modern Template** – Timeline-style with blue accents for creative roles

### 🌐 REST API
- **Production-ready FastAPI** server with comprehensive endpoints
- **Easy deployment** – Docker, Heroku, Railway, AWS, GCP, Azure support
- **File upload support** – Parse existing resumes via API
- **Background processing** – Automatic cleanup of temporary files

### ✅ Quality Assurance
- **Automatic validation** – Checks for content limits and invented information
- **Self-healing** – LLM-based fixes with emergency fallback corrections
- **Page limit enforcement** – Ensures one-page output with WeasyPrint validation

---

---

## 📁 Project Structure

```
automatic-cv/
├── app/
│   └── app.py                    # FastAPI REST API server
├── src/
│   ├── main.py                   # CLI entry point
│   ├── data_loader.py            # Profile JSON loader
│   ├── job_parser.py             # Job posting scraper
│   ├── llm_agent.py              # LLM integration & validation
│   ├── renderer.py               # PDF generation (HTML → PDF)
│   ├── cv_validator.py           # CV validation system
│   └── pdf_parser.py             # PDF resume extraction
├── templates/
│   ├── cv_template_tech.html     # Tech industry template
│   ├── cv_template_business.html # Business template
│   └── cv_template_modern.html   # Modern template
├── prompts/
│   ├── cv_optimization.txt       # CV optimization prompt
│   ├── cv_extraction.txt         # Resume parsing prompt
│   ├── cv_fix.txt                # Validation fix prompt
│   └── job_extraction.txt        # Job parsing prompt
├── data/
│   └── profile.json              # Your personal information
├── output/
│   └── temp/                     # Generated files
├── docker-compose.yml            # Docker deployment config
├── Dockerfile                    # Container image definition
├── requirements.txt              # Python dependencies
├── start_api.sh                  # API startup script
├── test_api_client.py            # API testing client
├── API_DOCUMENTATION.md          # Complete API docs
└── DEPLOYMENT.md                 # Deployment guide
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Replicate API Token** (get it from [replicate.com](https://replicate.com))
- **Tesseract OCR** (optional, for scanned PDFs)

### Installation

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
```

---

## 💻 CLI Usage

### Generate CV from Job URL

```bash
python src/main.py --url "https://linkedin.com/jobs/view/123456" --template modern
```

### Generate CV from Job Text File

```bash
# Save job description to data/job_description.txt
python src/main.py --template business
```

### Extract Data from Existing Resume

```bash
python src/main.py --resume
# Outputs structured JSON to data/profile_fetched.json
```

### CLI Options

```
--url URL              Job posting URL
--template TEMPLATE    Template style: tech, business, or modern (default: tech)
--resume               Extract CV data from PDF resume
--skip-validation      Skip CV validation and auto-correction
--max-retries N        Maximum validation retry attempts (default: 2)
```

---

## 🌐 REST API Usage

### Start the API Server

```bash
# Quick start
./start_api.sh

# Or manually
cd app
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **Base URL**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs (interactive Swagger UI)
- **Health Check**: http://localhost:8000/health

### API Endpoints

#### 1. Generate CV from Job URL
```bash
curl -X POST "http://localhost:8000/api/v1/cv/generate/url" \
  -H "Content-Type: application/json" \
  -d '{
    "job_url": "https://linkedin.com/jobs/view/123456",
    "template": "modern"
  }' \
  --output my_cv.pdf
```

#### 2. Generate CV from Job Text
```bash
curl -X POST "http://localhost:8000/api/v1/cv/generate/text" \
  -H "Content-Type: application/json" \
  -d '{
    "job_text": "We are looking for a Python developer...",
    "template": "tech"
  }' \
  --output my_cv.pdf
```

#### 3. Parse Existing Resume
```bash
curl -X POST "http://localhost:8000/api/v1/cv/parse" \
  -F "file=@my_resume.pdf"
```

#### 4. Extract Job Information
```bash
curl -X POST "http://localhost:8000/api/v1/job/extract" \
  -H "Content-Type: application/json" \
  -d '{"job_url": "https://example.com/job-posting"}'
```

### Python Client Example

```python
import requests

# Generate CV
response = requests.post(
    "http://localhost:8000/api/v1/cv/generate/url",
    json={
        "job_url": "https://linkedin.com/jobs/view/123456",
        "template": "modern"
    }
)

with open("generated_cv.pdf", "wb") as f:
    f.write(response.content)

print("CV generated successfully!")
```

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.

---

## 🐳 Docker Deployment

### Quick Deploy with Docker Compose

```bash
# Create .env file with your API token
echo "REPLICATE_API_TOKEN=your_token_here" > .env

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

### Manual Docker Build

```bash
docker build -t cv-generator-api .
docker run -d -p 8000:8000 -e REPLICATE_API_TOKEN=your_token cv-generator-api
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment guides.

---

## 📚 Documentation

- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete REST API reference
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guides for various platforms

---

## 🎨 Template Styles

### Tech Template (Default)
- Clean, minimalist design
- Perfect for software engineering roles
- Focuses on technical skills and projects

### Business Template
- Modern gradient elements
- Two-column card-based layout
- Ideal for corporate/business roles

### Modern Template
- Timeline-style layout
- Blue accent colors
- Great for creative/modern companies

---

## 🔧 Configuration

### Profile Data Format

Create `data/profile.json` with your information:

```json
{
  "personal_info": {
    "name": "Your Name",
    "email": "your.email@example.com",
    "phone": "+1234567890",
    "location": "City, State",
    "linkedin": "linkedin.com/in/yourprofile",
    "github": "github.com/yourusername"
  },
  "summary": "Brief professional summary...",
  "education": [
    {
      "degree": "B.S. Computer Science",
      "institution": "University Name",
      "graduation_date": "2020",
      "gpa": "3.8"
    }
  ],
  "experience": [
    {
      "title": "Software Engineer",
      "company": "Company Name",
      "start_date": "Jan 2020",
      "end_date": "Present",
      "descrition_list": [
        "Built scalable APIs using FastAPI",
        "Improved performance by 40%"
      ]
    }
  ],
  "projects": [
    {
      "name": "Project Name",
      "description": "Brief description",
      "technologies": ["Python", "FastAPI", "Docker"],
      "link": "github.com/user/project"
    }
  ],
  "skills": {
    "programming_languages": ["Python", "JavaScript"],
    "frameworks": ["FastAPI", "React"],
    "tools": ["Docker", "Git"],
    "soft_skills": ["Leadership", "Communication"]
  }
}
```

---

## 🧪 Testing

### Test the API

```bash
# Run test suite
python test_api_client.py

# Individual tests
curl http://localhost:8000/health
```

### Test the CLI

```bash
# Test CV generation
python src/main.py --url "https://example.com/job" --template tech

# Test resume parsing
python src/main.py --resume
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

[MIT License](LICENSE)

---

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/albertodian/automatic-cv/issues)
- **Documentation**: See API_DOCUMENTATION.md and DEPLOYMENT.md

---

## 🙏 Acknowledgments

- **Replicate** for LLM API access
- **FastAPI** for the excellent web framework
- **WeasyPrint** for HTML to PDF conversion
- **Community contributors**

---

Made with ❤️ by [Alberto Dian](https://github.com/albertodian)