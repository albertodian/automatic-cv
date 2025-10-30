# Web Interface Usage Guide

## Overview

The `index.html` file provides a user-friendly web interface for the Automatic CV Generator. It supports **two modes of operation**:

### Mode 1: Upload Resume (Recommended for new users)
1. Upload your PDF resume
2. System extracts your information automatically
3. Paste job description
4. Generate optimized CV

### Mode 2: Use Existing Profile (Quick & Easy)
1. **Skip the upload step** - Don't upload any file
2. Paste job description
3. Generate optimized CV
4. System automatically uses `data/profile.json`

## How It Works

### API Endpoints Used

#### When Resume is Uploaded:
```
POST /api/cv/extract
  ↓ (extracts profile data)
POST /api/cv/generate
  ↓ (uses extracted profile)
Returns optimized CV JSON
```

#### When Resume is NOT Uploaded:
```
POST /api/cv/generate-from-file
  ↓ (loads data/profile.json automatically)
Returns optimized CV JSON
```

## Step-by-Step Instructions

### Setup (One-time)

```bash
# 1. Clone and install
git clone https://github.com/albertodian/automatic-cv.git
cd automatic-cv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure environment
echo "REPLICATE_API_TOKEN=your_token_here" > .env

# 3. Make sure profile.json exists (optional but recommended)
# Edit data/profile.json with your information
```

### Using the Web Interface

```bash
# 1. Start the API server
python app/app.py

# 2. Open the web interface
open index.html  # macOS
# or
python -m http.server 3000  # Then visit http://localhost:3000
```

### Option A: With Resume Upload

1. **Drag & drop** your PDF resume or click to upload
2. Wait for extraction confirmation (✅ Resume data extracted successfully!)
3. **Paste** the job description in the text area
4. Click **"Generate Optimized CV"**
5. Wait 30-60 seconds for AI processing
6. View the optimized CV JSON in the success message

### Option B: Without Resume Upload (Using profile.json)

1. **Skip** the upload step entirely
2. **Paste** the job description in the text area
3. Click **"Generate Optimized CV"**
4. System automatically uses `data/profile.json`
5. Wait 30-60 seconds for AI processing
6. View the optimized CV JSON in the success message

## Features

### Smart Detection
- ✅ Automatically detects if resume was uploaded
- ✅ Falls back to `profile.json` if no upload
- ✅ Clear status messages for each operation

### User-Friendly Interface
- 📱 Responsive design (works on mobile & desktop)
- 🎨 Modern, clean UI with smooth animations
- 📊 Real-time progress indicators
- ⚠️ Clear error messages and guidance

### Robust Error Handling
- File validation (PDF only, max 10MB)
- API connection checks on page load
- Detailed error messages
- Automatic fallback mechanisms

## API Response Format

The generated CV is returned as JSON:

```json
{
  "success": true,
  "profile": {
    "personal_info": {...},
    "summary": "...",
    "education": [...],
    "experience": [...],
    "projects": [...],
    "skills": [...]
  },
  "message": "CV successfully generated! ATS Score: 92.5% (Iterations: 2)"
}
```

## Troubleshooting

### "Cannot connect to API" Error
**Solution:** Make sure the server is running
```bash
python app/app.py
```

### "Profile file not found" Error
**Solution:** Create or check `data/profile.json`
```bash
# Check if file exists
ls -la data/profile.json

# Copy example if needed
cp data/profile.example.json data/profile.json
```

### "Failed to extract CV" Error
**Solution:** 
- Check PDF is not corrupted
- Ensure PDF contains text (not just images)
- Try with a different PDF

### Slow Generation Time
**Normal:** CV generation takes 30-60 seconds due to:
- RAG database indexing
- LLM optimization (multiple iterations)
- ATS scoring and refinement

## Configuration Options

### Change API Base URL
Edit line 307 in `index.html`:
```javascript
const API_BASE_URL = 'http://localhost:8000';  // Change this
```

### Change Template Style
Edit the API call in `index.html` (lines 470 & 485):
```javascript
template: 'tech',  // Options: 'tech', 'business', 'modern'
```

### Change LLM Model
Edit the API call in `index.html` (lines 471 & 486):
```javascript
model_name: 'openai/gpt-4.1-mini',  // Change model here
```

## Advanced Usage

### Custom Profile Path
If you want to use a different profile file, you can modify the API call:

```javascript
body: JSON.stringify({
    profile_path: 'custom/path/to/profile.json',  // Custom path
    job_description: jobDesc,
    template: 'tech',
    model_name: 'openai/gpt-4.1-mini'
})
```

### Direct API Integration
You can also call the API directly without the web interface:

```bash
# Using profile.json
curl -X POST "http://localhost:8000/api/cv/generate-from-file" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_path": "data/profile.json",
    "job_description": "Your job description here...",
    "template": "tech"
  }'
```

## Benefits of Using profile.json

✅ **Faster:** No need to upload and extract PDF every time
✅ **Consistent:** Same profile data for all jobs
✅ **Easy Updates:** Just edit one JSON file
✅ **Version Control:** Can track changes with Git
✅ **Automation:** Perfect for batch processing multiple jobs

## Next Steps

After generating the CV JSON:

1. **Save the JSON** - Copy from the success message
2. **Render to PDF** - Use `/api/cv/render-stream` endpoint
3. **Apply to job** - Download and submit your optimized CV

## Support

- 📖 [Full API Documentation](docs/API_DOCUMENTATION.md)
- 🐛 [Report Issues](https://github.com/albertodian/automatic-cv/issues)
- 📧 Contact: albertodian.ad@gmail.com
