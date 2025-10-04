# API Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATIONS                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │   Web App   │  │   Mobile    │  │   CLI Tool  │  │  Webhook   │ │
│  │  (Browser)  │  │     App     │  │   (Python)  │  │ Integrator │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
│         │                │                │                │         │
└─────────┼────────────────┼────────────────┼────────────────┼─────────┘
          │                │                │                │
          │                └────────┬───────┘                │
          │                         │                        │
          └─────────────────────────┼────────────────────────┘
                                    │
                    HTTP/HTTPS (JSON, PDF, multipart/form-data)
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          FASTAPI SERVER                              │
│                        (app/app.py)                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    API ENDPOINTS                              │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  GET  /                        │ API info                     │  │
│  │  GET  /health                  │ Health check                 │  │
│  │  POST /api/v1/cv/generate/url  │ Generate from job URL        │  │
│  │  POST /api/v1/cv/generate/text │ Generate from job text       │  │
│  │  POST /api/v1/cv/parse         │ Parse PDF resume            │  │
│  │  POST /api/v1/job/extract      │ Extract job info            │  │
│  │  POST /api/v1/cv/generate/custom│ Custom profile generation   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                    │                                │
│                                    ▼                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  MIDDLEWARE LAYER                             │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  • CORS Handler                                               │  │
│  │  • Error Handler                                              │  │
│  │  • Request Validation (Pydantic)                             │  │
│  │  • Background Tasks                                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                    │                                │
└────────────────────────────────────┼────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        CORE PROCESSING LAYER                         │
│                         (src/ modules)                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────────┐          │
│  │ job_parser.py │  │data_loader.py │  │ pdf_parser.py  │          │
│  ├───────────────┤  ├───────────────┤  ├────────────────┤          │
│  │ • Fetch URLs  │  │ • Load JSON   │  │ • PyPDF2       │          │
│  │ • Scrape jobs │  │ • Validate    │  │ • pdfplumber   │          │
│  │ • Clean text  │  │               │  │ • PyMuPDF      │          │
│  │               │  │               │  │ • OCR fallback │          │
│  └───────────────┘  └───────────────┘  └────────────────┘          │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    llm_agent.py                                │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │ • CV Optimization    • Job Extraction                         │  │
│  │ • CV Validation      • Error Correction                       │  │
│  │ • Resume Parsing     • Content Fixing                         │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                    │                                │
│                                    ▼                                │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                  cv_validator.py                               │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │ • Page count validation                                        │  │
│  │ • Content limit checks                                         │  │
│  │ • Hallucination detection                                      │  │
│  │ • Auto-correction                                              │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                    │                                │
│                                    ▼                                │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    renderer.py                                 │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │ • Jinja2 templating                                            │  │
│  │ • HTML generation                                              │  │
│  │ • WeasyPrint PDF conversion                                    │  │
│  │ • Template selection (tech/business/modern)                   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                       │
└───────────────────────────────────────────────────────────┬───────────┘
                                                             │
                                                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL SERVICES                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Replicate API   │  │  Web Scraping    │  │  File System     │  │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤  │
│  │ • GPT-4.1-mini   │  │ • BeautifulSoup  │  │ • Temp files     │  │
│  │ • LLM processing │  │ • Playwright     │  │ • Data storage   │  │
│  │ • CV optimization│  │ • Scrapy         │  │ • Output PDFs    │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘


                        DATA FLOW EXAMPLE
                        ─────────────────

   Job URL Input
        │
        ▼
   ┌─────────────┐
   │ Fetch & Parse│  ────────►  Raw job text
   └─────────────┘
        │
        ▼
   ┌─────────────┐
   │ LLM Extract  │  ────────►  Structured job info
   └─────────────┘              (title, requirements, keywords)
        │
        ▼
   ┌─────────────┐
   │ Load Profile │  ────────►  Candidate data
   └─────────────┘              (experience, skills, projects)
        │
        ▼
   ┌─────────────┐
   │ LLM Optimize │  ────────►  Tailored CV data
   └─────────────┘              (keyword-matched, ATS-friendly)
        │
        ▼
   ┌─────────────┐
   │  Validate    │  ────────►  Check page limits
   └─────────────┘              Verify no hallucinations
        │                       Auto-correct if needed
        │ (if invalid)
        ├───────►  LLM Fix  ───►  Corrected data
        │
        ▼
   ┌─────────────┐
   │   Render     │  ────────►  PDF file
   └─────────────┘              (tech/business/modern template)
        │
        ▼
   Return to Client


                    DEPLOYMENT ARCHITECTURE
                    ────────────────────────

                    ┌─────────────────┐
                    │   Load Balancer │
                    │    (Optional)   │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
        ┌───────▼────────┐       ┌───────▼────────┐
        │  API Instance 1│       │  API Instance 2│
        │  (Docker/VM)   │       │  (Docker/VM)   │
        └───────┬────────┘       └───────┬────────┘
                │                         │
                └────────────┬────────────┘
                             │
                    ┌────────▼────────┐
                    │  Shared Storage │
                    │   (if needed)   │
                    └─────────────────┘


               DOCKER COMPOSE ARCHITECTURE
               ─────────────────────────────

    ┌──────────────────────────────────────────┐
    │         Docker Host                      │
    ├──────────────────────────────────────────┤
    │                                          │
    │  ┌────────────┐      ┌───────────────┐  │
    │  │   Nginx    │      │   CV API      │  │
    │  │ Container  │◄─────┤   Container   │  │
    │  │ (Port 80)  │      │  (Port 8000)  │  │
    │  └─────┬──────┘      └───────┬───────┘  │
    │        │                     │           │
    │  ┌─────▼──────────────────────▼───────┐ │
    │  │     Shared Volumes                 │ │
    │  │  • data/                           │ │
    │  │  • output/                         │ │
    │  │  • templates/                      │ │
    │  └────────────────────────────────────┘ │
    │                                          │
    └──────────────────────────────────────────┘


                  FILE STRUCTURE
                  ───────────────

    automatic-cv/
    │
    ├── app/
    │   └── app.py .......................... FastAPI server (500+ lines)
    │
    ├── src/
    │   ├── main.py ........................ CLI entry point
    │   ├── llm_agent.py ................... LLM integration & validation
    │   ├── job_parser.py .................. Job scraping
    │   ├── data_loader.py ................. Profile loading
    │   ├── renderer.py .................... PDF generation
    │   ├── cv_validator.py ................ Validation logic
    │   └── pdf_parser.py .................. Resume parsing
    │
    ├── templates/
    │   ├── cv_template_tech.html .......... Tech template
    │   ├── cv_template_business.html ...... Business template
    │   └── cv_template_modern.html ........ Modern template
    │
    ├── prompts/
    │   ├── cv_optimization.txt ............ Optimization prompt
    │   ├── cv_extraction.txt .............. Extraction prompt
    │   ├── cv_fix.txt ..................... Fix prompt
    │   └── job_extraction.txt ............. Job parsing prompt
    │
    ├── Documentation/
    │   ├── README.md ...................... Main documentation
    │   ├── API_DOCUMENTATION.md ........... Complete API reference
    │   ├── DEPLOYMENT.md .................. Deployment guides
    │   ├── API_QUICKREF.md ................ Quick reference
    │   └── API_IMPLEMENTATION_SUMMARY.md .. This summary
    │
    ├── Deployment/
    │   ├── Dockerfile ..................... Container definition
    │   ├── docker-compose.yml ............. Multi-container setup
    │   ├── nginx.conf ..................... Reverse proxy config
    │   ├── .env.example ................... Environment template
    │   └── start_api.sh ................... Startup script
    │
    ├── Testing/
    │   ├── test_api_client.py ............. Test suite
    │   └── web_demo.html .................. Interactive demo
    │
    └── Configuration/
        ├── requirements.txt ............... Python dependencies
        ├── .gitignore ..................... Git ignore rules
        └── .env ........................... Environment variables


                  TECH STACK
                  ──────────

    Backend:
    • FastAPI ............... Web framework
    • Uvicorn ............... ASGI server
    • Pydantic .............. Data validation
    • Replicate API ......... LLM access

    Document Processing:
    • WeasyPrint ............ HTML → PDF
    • PyPDF2, pdfplumber .... PDF parsing
    • PyMuPDF ............... Advanced parsing
    • pytesseract ........... OCR

    Web Scraping:
    • BeautifulSoup ......... HTML parsing
    • Playwright ............ Browser automation
    • Scrapy ................ Web crawling

    Template Engine:
    • Jinja2 ................ HTML templating

    Deployment:
    • Docker ................ Containerization
    • Nginx ................. Reverse proxy
    • Systemd ............... Service management


            MONITORING & OBSERVABILITY
            ───────────────────────────

    ┌─────────────────────────────────────┐
    │  Application Logs                   │
    │  • Request/Response logging         │
    │  • Error tracking                   │
    │  • Performance metrics              │
    └─────────┬───────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │  Health Checks                      │
    │  • GET /health                      │
    │  • Uptime monitoring                │
    │  • Service status                   │
    └─────────┬───────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────┐
    │  External Monitoring (Optional)     │
    │  • Sentry (errors)                  │
    │  • DataDog (metrics)                │
    │  • New Relic (APM)                  │
    └─────────────────────────────────────┘


        SECURITY CONSIDERATIONS
        ────────────────────────

    ✓ Input Validation ....... Pydantic models
    ✓ CORS Configuration ..... Configured origins
    ✓ File Upload Limits ..... Size restrictions
    ✓ Error Sanitization ..... No sensitive data leaks
    ✓ HTTPS Support .......... Nginx SSL config
    ⊕ API Authentication ..... Optional (see docs)
    ⊕ Rate Limiting .......... Optional (see docs)
    ⊕ Request Signing ........ Optional
```

**Legend:**
- `✓` Implemented
- `⊕` Optional/Recommended for production
- `→` Data flow
- `◄─` Request/Response

---

**Last Updated**: October 2025  
**Version**: 1.0.0  
**Status**: Production Ready
