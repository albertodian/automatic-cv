"""
REST API for Automatic CV Generation
Provides endpoints for CV optimization, PDF parsing, and document generation.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
import sys
import os
import json
import uuid
import shutil
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_loader import load_profile
from job_parser import fetch_job_description
from llm_agent import (
    generate_optimized_profile_with_validation,
    extract_relevant_job_info,
    extract_cv_from_pdf_smart,
    save_cv_to_json
)
from renderer import render_cv_pdf_html

# Initialize FastAPI app
app = FastAPI(
    title="Automatic CV Generator API",
    description="AI-powered CV optimization and generation service",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create temp directories
TEMP_DIR = os.path.join(os.path.dirname(__file__), '..', 'output', 'temp_api')
os.makedirs(TEMP_DIR, exist_ok=True)

# ==================== Pydantic Models ====================

class JobURLRequest(BaseModel):
    """Request model for job URL processing"""
    job_url: HttpUrl = Field(..., description="URL of the job posting")
    template: str = Field(default="tech", description="CV template: tech, business, or modern")
    skip_validation: bool = Field(default=False, description="Skip CV validation")
    max_retries: int = Field(default=2, ge=0, le=5, description="Max validation retries")

class JobTextRequest(BaseModel):
    """Request model for direct job text processing"""
    job_text: str = Field(..., description="Raw job description text")
    template: str = Field(default="tech", description="CV template: tech, business, or modern")
    skip_validation: bool = Field(default=False, description="Skip CV validation")
    max_retries: int = Field(default=2, ge=0, le=5, description="Max validation retries")

class ProfileData(BaseModel):
    """Request model for custom profile data"""
    personal_info: dict
    summary: str
    education: List[dict]
    experience: List[dict]
    projects: List[dict]
    skills: dict

class CVGenerationRequest(BaseModel):
    """Request model for CV generation with custom profile"""
    profile: ProfileData
    job_text: str
    template: str = Field(default="tech", description="CV template")
    skip_validation: bool = Field(default=False)
    max_retries: int = Field(default=2, ge=0, le=5)

class StatusResponse(BaseModel):
    """Response model for operation status"""
    status: str
    message: str
    job_id: Optional[str] = None
    data: Optional[dict] = None

# ==================== Helper Functions ====================

def cleanup_temp_file(file_path: str):
    """Background task to cleanup temporary files"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Cleaned up temp file: {file_path}")
    except Exception as e:
        print(f"Error cleaning up {file_path}: {e}")

def generate_job_id() -> str:
    """Generate unique job ID"""
    return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

def get_default_profile() -> dict:
    """Load default profile from data/profile.json"""
    profile_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'profile.json')
    return load_profile(profile_path)

# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Automatic CV Generator API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "generate_from_url": "/api/v1/cv/generate/url",
            "generate_from_text": "/api/v1/cv/generate/text",
            "parse_resume": "/api/v1/cv/parse",
            "extract_job_info": "/api/v1/job/extract"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "cv-generator-api"
    }

@app.post("/api/v1/cv/generate/url", response_class=FileResponse)
async def generate_cv_from_url(
    request: JobURLRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate optimized CV from job posting URL
    
    Returns PDF file of the generated CV
    """
    job_id = generate_job_id()
    
    try:
        print(f"[{job_id}] Starting CV generation from URL: {request.job_url}")
        
        # Fetch job description
        print(f"[{job_id}] Fetching job description...")
        job_text = fetch_job_description(str(request.job_url))
        
        # Extract job info
        print(f"[{job_id}] Extracting job information...")
        job_info = extract_relevant_job_info(job_text, "openai/gpt-4.1-mini")
        
        # Load default profile
        print(f"[{job_id}] Loading candidate profile...")
        profile = get_default_profile()
        
        # Generate optimized CV
        print(f"[{job_id}] Generating optimized CV...")
        if request.skip_validation:
            from llm_agent import generate_optimized_profile
            final_profile = generate_optimized_profile(profile, job_info, "openai/gpt-4.1-mini")
        else:
            final_profile = generate_optimized_profile_with_validation(
                profile=profile,
                job_info=job_info,
                model_name="openai/gpt-4.1-mini",
                max_retries=request.max_retries
            )
        
        # Render PDF
        print(f"[{job_id}] Rendering PDF...")
        output_path = os.path.join(TEMP_DIR, f"cv_{job_id}.pdf")
        render_cv_pdf_html(final_profile, template=request.template, output_path=output_path)
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_temp_file, output_path)
        
        print(f"[{job_id}] CV generation complete!")
        
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=f"CV_{job_info.get('company', 'optimized')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        
    except Exception as e:
        print(f"[{job_id}] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CV generation failed: {str(e)}")

@app.post("/api/v1/cv/generate/text", response_class=FileResponse)
async def generate_cv_from_text(
    request: JobTextRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate optimized CV from job description text
    
    Returns PDF file of the generated CV
    """
    job_id = generate_job_id()
    
    try:
        print(f"[{job_id}] Starting CV generation from text")
        
        # Extract job info
        print(f"[{job_id}] Extracting job information...")
        job_info = extract_relevant_job_info(request.job_text, "openai/gpt-4.1-mini")
        
        # Load default profile
        print(f"[{job_id}] Loading candidate profile...")
        profile = get_default_profile()
        
        # Generate optimized CV
        print(f"[{job_id}] Generating optimized CV...")
        if request.skip_validation:
            from llm_agent import generate_optimized_profile
            final_profile = generate_optimized_profile(profile, job_info, "openai/gpt-4.1-mini")
        else:
            final_profile = generate_optimized_profile_with_validation(
                profile=profile,
                job_info=job_info,
                model_name="openai/gpt-4.1-mini",
                max_retries=request.max_retries
            )
        
        # Render PDF
        print(f"[{job_id}] Rendering PDF...")
        output_path = os.path.join(TEMP_DIR, f"cv_{job_id}.pdf")
        render_cv_pdf_html(final_profile, template=request.template, output_path=output_path)
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_temp_file, output_path)
        
        print(f"[{job_id}] CV generation complete!")
        
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=f"CV_optimized_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        
    except Exception as e:
        print(f"[{job_id}] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CV generation failed: {str(e)}")

@app.post("/api/v1/cv/parse", response_model=StatusResponse)
async def parse_resume_pdf(
    file: UploadFile = File(..., description="PDF resume file to parse"),
    background_tasks: BackgroundTasks = None
):
    """
    Parse PDF resume and extract structured data
    
    Returns JSON with extracted CV information
    """
    job_id = generate_job_id()
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    temp_pdf_path = os.path.join(TEMP_DIR, f"upload_{job_id}.pdf")
    
    try:
        print(f"[{job_id}] Parsing uploaded resume: {file.filename}")
        
        # Save uploaded file
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract CV data
        print(f"[{job_id}] Extracting CV data...")
        cv_data = extract_cv_from_pdf_smart(temp_pdf_path, "openai/gpt-4.1-mini")
        
        # Cleanup
        if background_tasks:
            background_tasks.add_task(cleanup_temp_file, temp_pdf_path)
        else:
            os.remove(temp_pdf_path)
        
        print(f"[{job_id}] Resume parsing complete!")
        
        return StatusResponse(
            status="success",
            message="Resume parsed successfully",
            job_id=job_id,
            data=cv_data
        )
        
    except Exception as e:
        # Cleanup on error
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        print(f"[{job_id}] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Resume parsing failed: {str(e)}")

@app.post("/api/v1/job/extract", response_model=StatusResponse)
async def extract_job_information(
    job_url: Optional[str] = None,
    job_text: Optional[str] = None
):
    """
    Extract structured information from job posting
    
    Provide either job_url or job_text
    """
    job_id = generate_job_id()
    
    if not job_url and not job_text:
        raise HTTPException(
            status_code=400,
            detail="Either job_url or job_text must be provided"
        )
    
    try:
        print(f"[{job_id}] Extracting job information...")
        
        # Fetch job text if URL provided
        if job_url:
            print(f"[{job_id}] Fetching from URL: {job_url}")
            job_text = fetch_job_description(job_url)
        
        # Extract job info
        job_info = extract_relevant_job_info(job_text, "openai/gpt-4.1-mini")
        
        print(f"[{job_id}] Job extraction complete!")
        
        return StatusResponse(
            status="success",
            message="Job information extracted successfully",
            job_id=job_id,
            data=job_info
        )
        
    except Exception as e:
        print(f"[{job_id}] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Job extraction failed: {str(e)}")

@app.post("/api/v1/cv/generate/custom", response_class=FileResponse)
async def generate_cv_with_custom_profile(
    request: CVGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate CV with custom profile data
    
    Allows full control over profile information
    """
    job_id = generate_job_id()
    
    try:
        print(f"[{job_id}] Starting CV generation with custom profile")
        
        # Convert Pydantic model to dict
        profile = request.profile.dict()
        
        # Extract job info
        print(f"[{job_id}] Extracting job information...")
        job_info = extract_relevant_job_info(request.job_text, "openai/gpt-4.1-mini")
        
        # Generate optimized CV
        print(f"[{job_id}] Generating optimized CV...")
        if request.skip_validation:
            from llm_agent import generate_optimized_profile
            final_profile = generate_optimized_profile(profile, job_info, "openai/gpt-4.1-mini")
        else:
            final_profile = generate_optimized_profile_with_validation(
                profile=profile,
                job_info=job_info,
                model_name="openai/gpt-4.1-mini",
                max_retries=request.max_retries
            )
        
        # Render PDF
        print(f"[{job_id}] Rendering PDF...")
        output_path = os.path.join(TEMP_DIR, f"cv_{job_id}.pdf")
        render_cv_pdf_html(final_profile, template=request.template, output_path=output_path)
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_temp_file, output_path)
        
        print(f"[{job_id}] CV generation complete!")
        
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=f"CV_custom_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        
    except Exception as e:
        print(f"[{job_id}] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CV generation failed: {str(e)}")

# ==================== Error Handlers ====================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "message": "Endpoint not found",
            "path": str(request.url)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc)
        }
    )

# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )