# Automatic CV Generator 🚀

An intelligent **RAG-powered CV optimization system** that uses **Retrieval-Augmented Generation** to create perfectly tailored, ATS-optimized CVs for any job posting. Combines semantic search with LLMs for maximum relevance and precision.

> **🚂 Production-ready on Railway** - Handles 60-150s LLM + PDF generation without timeouts!

## ✨ Key Features

### � RAG-Powered Intelligence
- **Semantic content retrieval** – Uses ChromaDB vector database with sentence transformers
- **Smart experience/project selection** – Retrieves only the most relevant items per job
- **Synonym-aware matching** – Understands "ML" = "Machine Learning" = "model training"
- **Relevance scoring** – Combines semantic similarity + keyword overlap + recency

### 🤖 AI-Driven Optimization
- **LLM-based enhancement** – GPT-4.1-mini (via Replicate) for natural language generation
- **Iterative ATS refinement** – Automatically improves to 90%+ ATS compatibility score
- **Keyword density optimization** – Ensures 3-5 mentions of critical keywords
- **Structure validation** – Guarantees correct JSON format for template rendering

### 📄 Advanced Resume Processing
- **Multi-method PDF parsing** – pdfplumber, PyMuPDF, PyPDF2, OCR (Tesseract) fallback
- **Intelligent job scraping** – Playwright-based extraction from LinkedIn, Indeed, etc.
- **Smart field normalization** – Handles inconsistent date formats and field names

### 🎨 Professional Templates
- **Tech Template** – Clean, minimalist design for engineering roles
- **Business Template** – Modern gradient with two-column layout
- **Modern Template** – Timeline-style with blue accents

### 🌐 Production-Ready API
- **FastAPI REST API** with 8 endpoints for all operations
- **Railway-optimized** – No timeouts, perfect for 60-150s LLM workflows
- **File upload support** – Parse and generate CVs via HTTP
- **Comprehensive docs** – Auto-generated Swagger/OpenAPI

---

## 🔬 How It Works: The Pipeline

### Architecture Overview

```
Job URL → Job Parser → RAG System → LLM Generator → ATS Optimizer → PDF Renderer
   ↓          ↓            ↓             ↓              ↓              ↓
 Text      Keywords   Relevant      Optimized      90%+ Score    Final PDF
Extract   Analysis   Content       Profile        Validation
```

### Detailed Pipeline

#### 1. **Job Information Extraction** (`job_parser.py`)
```python
Input:  Job URL or raw text
Tools:  Playwright (web scraping)
LLM:    GPT-4.1-mini (structure extraction)
Output: {title, company, keywords[], requirements[], responsibilities[]}
```
- Scrapes job posting content from any URL
- Uses LLM to extract structured information
- Identifies 10-15 critical keywords for matching

#### 2. **RAG Content Retrieval** (`rag_system.py`)
```python
Input:  User profile + job keywords
Tools:  ChromaDB (vector database)
        Sentence-Transformers (all-MiniLM-L6-v2)
Method: Semantic similarity + keyword matching + recency scoring
Output: Top 3 experiences + Top 4 projects (pre-filtered)
```
- **Indexing Phase**:
  - Embeds all experiences, projects, skills into vector space
  - Stores in persistent ChromaDB collection
  
- **Retrieval Phase**:
  - Semantic search for experiences matching job requirements
  - Hybrid scoring: `0.4*semantic + 0.4*keywords + 0.2*recency`
  - Retrieves only most relevant content (prevents hallucination)

#### 3. **LLM-Based Generation** (`llm_agent.py`)
```python
Input:  RAG-filtered profile + job info
LLM:    GPT-4.1-mini via Replicate API
Prompt: cv_optimization_rag.txt (2000+ tokens)
Output: Optimized JSON profile
```
- Uses pre-filtered content from RAG (no need to select)
- Focuses on keyword weaving and enhancement
- Generates 2-sentence summary with 4-5 keywords
- Preserves all provided experiences/projects

#### 4. **Structure Validation** (`structure_validator.py`)
```python
Checks:
  ✓ experience[].years (not "date")
  ✓ experience[].descrition_list (with typo!)
  ✓ projects[].year (singular)
  ✓ projects[].description (string, no typo)
  ✓ No missing entries
  
Actions: Auto-fix field names, restore removed entries
```
- Ensures JSON matches template expectations
- Handles LLM inconsistencies automatically
- Validates required fields exist

#### 5. **ATS Optimization** (`ats_optimizer.py`, `ats_refiner.py`)
```python
Scoring: 60% keyword match + 20% density + 20% structure
Target:  90%+ ATS compatibility
Method:  Iterative refinement (max 3 iterations)
```
- **Initial optimization**: Expands abbreviations (ML → Machine Learning)
- **Iterative refinement**:
  - Calculates current ATS score
  - Identifies missing/under-represented keywords
  - LLM enhances descriptions with keywords
  - Repeats until 90%+ or max iterations
  - Preserves structure (no new entries)

#### 6. **PDF Rendering** (`renderer.py`)
```python
Input:  Final validated JSON
Method: Jinja2 templates → HTML → WeasyPrint → PDF
Output: ATS-friendly single-page PDF
```
- Selects template (tech/business/modern)
- Renders HTML from Jinja2 template
- Converts to PDF with WeasyPrint
- Validates single-page output

---

## 🛠️ Tech Stack

### Core Technologies
- **Python 3.10+** – Primary language
- **FastAPI** – REST API framework
- **Replicate API** – LLM access (GPT-4.1-mini)

### RAG & Embeddings
- **ChromaDB** – Vector database for semantic search
- **Sentence-Transformers** – Embedding model (all-MiniLM-L6-v2)
- **NumPy** – Vector operations

### Data Processing
- **Playwright** – Job posting web scraping
- **pdfplumber, PyMuPDF, PyPDF2** – PDF text extraction
- **Tesseract OCR** – Scanned PDF support (optional)

### PDF Generation
- **Jinja2** – HTML templating
- **WeasyPrint** – HTML to PDF conversion
- **CSS3** – Professional styling

### Deployment
- **Railway** – Cloud hosting (recommended)
- **Docker** – Containerization
- **Gunicorn** – Production WSGI server

---

## 📁 Project Structure

```
automatic-cv/
├── src/
│   ├── main_rag.py              # 🚀 Main RAG-enhanced CLI entry point
│   ├── rag_system.py            # 🧠 RAG retrieval & semantic search
│   ├── llm_agent.py             # 🤖 LLM generation & validation
│   ├── ats_optimizer.py         # 📊 ATS scoring algorithms
│   ├── ats_refiner.py           # 🔄 Iterative ATS refinement
│   ├── structure_validator.py   # ✅ JSON structure validation
│   ├── data_loader.py           # 📂 Profile loading & normalization
│   ├── job_parser.py            # 🌐 Job scraping (Playwright)
│   └── renderer.py              # 🎨 PDF generation (Jinja2 + WeasyPrint)
├── app/
│   └── app.py                   # 🌐 FastAPI REST API server
├── templates/
│   ├── cv_template_tech.html    # Tech template
│   ├── cv_template_business.html # Business template
│   └── cv_template_modern.html  # Modern template
├── prompts/
│   ├── cv_optimization_rag.txt  # RAG-enhanced optimization prompt
│   ├── cv_extraction.txt        # PDF resume parsing prompt
│   ├── cv_fix.txt               # LLM-based correction prompt
│   └── job_extraction.txt       # Job info extraction prompt
├── data/
│   ├── profile.json             # Your master profile
│   └── chroma_db/               # Persistent vector database
├── output/
│   ├── cv_output_rag.pdf        # Final generated CV
│   └── temp/                    # Intermediate JSON files
├── docs/
│   ├── FIELD_SCHEMA_REFERENCE.md # JSON field requirements
│   └── ATS_RESEARCH.md          # ATS optimization notes
├── Dockerfile                   # Container definition
├── railway.json                 # Railway deployment config
├── requirements.txt             # Python dependencies
└── README.md                    # This file
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

### Generate RAG-Enhanced CV from Job URL

```bash
python src/main_rag.py --url "https://linkedin.com/jobs/view/123456" --template modern
```

**What happens:**
1. Scrapes job posting → extracts keywords
2. RAG retrieves your 3 most relevant experiences + 4 best projects
3. LLM optimizes descriptions with job keywords
4. ATS refiner iterates until 90%+ compatibility
5. Generates professional PDF

### Generate from Saved Job Description

```bash
# Save job text to data/job_description.txt
python src/main_rag.py --template tech
```

### Extract Your Resume from PDF

```bash
python src/main_rag.py --resume
# Extracts structured data to data/profile_fetched.json
# Automatically resets RAG database with new content
```

### CLI Options

```bash
--url URL                    Job posting URL
--template STYLE             tech | business | modern (default: tech)
--resume                     Extract CV from PDF resume
--reset-rag                  Reset vector database (force reindex)
--no-rag                     Disable RAG (use all content)
--skip-validation            Skip validation (not recommended)
--max-retries N              Validation retries (default: 2)
--embedding-model MODEL      Sentence transformer model (default: all-MiniLM-L6-v2)
```

### Example Workflow

```bash
# 1. Extract your resume once
python src/main_rag.py --resume

# 2. Generate tailored CVs for different jobs
python src/main_rag.py --url "https://linkedin.com/jobs/ml-engineer" --template tech
python src/main_rag.py --url "https://indeed.com/backend-developer" --template business

# 3. Check intermediate outputs
cat output/temp/optimized_profile_rag.json  # Final JSON
cat output/temp/ats_report.json             # ATS analysis
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

## ☁️ Cloud Deployment

### 🚂 Deploy to Railway (Recommended)

**Railway is perfect for this app** - no timeout limits, no cold starts, $5/month:

```bash
# Quick Deploy (3 minutes)
# 1. Go to https://railway.app/new
# 2. Select your GitHub repo
# 3. Add environment variable: REPLICATE_API_TOKEN
# 4. Your API is live!

# OR via Railway CLI
npm install -g @railway/cli
railway login
railway init
railway variables set REPLICATE_API_TOKEN=your_token
railway up
```

Your API will be live at: `https://your-app.up.railway.app`

✅ **Why Railway?**
- ∞ Unlimited timeout (Vercel has 60s limit)
- No cold starts (always fast)
- Better for PDF/LLM processing (60-150s)
- $5/month flat rate

📚 **Complete guide:** [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) - Everything in one file!

### Alternative: Docker (Self-Hosted)

```bash
# Create .env file
echo "REPLICATE_API_TOKEN=your_token_here" > .env

# Start service
docker-compose up -d

# View logs
docker-compose logs -f
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for other options (AWS, GCP, Azure).

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