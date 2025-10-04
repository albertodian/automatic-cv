# FastAPI Application

**Complete REST API for Automatic CV Generation**

## 📁 Files

- **`app.py`** - Main FastAPI application (460+ lines, 8 endpoints)
- **`config.py`** - ⚙️ **Centralized configuration** (fully integrated!)
- **`start.py`** - Startup script with system checks
- **`test_api.py`** - Automated API tests
- **`example_client.py`** - Python client with usage examples
- **`API_DOCUMENTATION.md`** - **📖 Complete API documentation (READ THIS!)**

## ⚙️ Configuration

The API uses **centralized configuration** from `config.py`. All settings (server, CORS, LLM, templates) are now integrated and easy to customize. See the Configuration section in `API_DOCUMENTATION.md` for details.

## 🚀 Quick Start

```bash
# 1. Install dependencies (from project root)
pip install -r requirements.txt

# 2. Start the API
python start.py

# 3. Open docs
# Visit: http://localhost:8000/docs
```

## 📚 Documentation

**For complete API documentation, examples, and troubleshooting:**

👉 **Read [`API_DOCUMENTATION.md`](API_DOCUMENTATION.md)**

It contains everything you need:
- API endpoints reference
- Usage examples (Python, JavaScript, cURL)
- Request/response schemas
- Testing guide
- Troubleshooting
- Deployment instructions
- Architecture overview

## 🧪 Quick Test

```bash
python test_api.py
```

## 💻 Example Usage

```python
import requests

# Generate CV from job URL
response = requests.post(
    "http://localhost:8000/api/cv/generate-from-url",
    json={
        "profile": profile_data,
        "job_url": "https://example.com/job",
        "template": "tech"
    }
)

optimized_cv = response.json()['profile']
```

## 📊 Status

✅ **Production Ready**  
✅ **8 Endpoints Working**  
✅ **All Tests Passing**  
✅ **Fully Documented**

---

**For detailed information, see [`API_DOCUMENTATION.md`](API_DOCUMENTATION.md)**
