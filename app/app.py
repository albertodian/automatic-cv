"""
FastAPI application for automatic CV generation.

This API provides endpoints to:
- Generate optimized CVs based on job descriptions
- Extract CV data from PDF resumes
- Fetch job descriptions from URLs
- Render CVs to PDF format
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
import sys
import os
import json
import tempfile
from pathlib import Path

# Import configuration settings first (before changing directory)
sys.path.insert(0, os.path.dirname(__file__))
from config import settings

# Add parent directory to path to import from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Change working directory to project root for proper file access
# (needed for prompts, templates, etc.)
project_root = os.path.join(os.path.dirname(__file__), '..')
os.chdir(project_root)

from src.data_loader import load_profile
from src.job_parser import fetch_job_description
from src.llm_agent import (
    generate_optimized_profile_with_validation,
    extract_relevant_job_info,
    extract_cv_from_pdf_smart,
)
from src.renderer import render_cv_pdf_html, render_cover_letter_pdf

# Initialize FastAPI app with settings from config
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - configured from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# ============================================================================
# Pydantic Models (Request/Response schemas)
# ============================================================================

class PersonalInfo(BaseModel):
    """Personal information schema"""
    name: str
    email: str
    phone: str
    nationality: Optional[str] = None
    age: Optional[int] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    languages: Optional[List[str]] = None

class Education(BaseModel):
    """Education entry schema"""
    degree: str
    institution: str
    location: str
    year: str
    description: Optional[str] = None
    grade: Optional[str] = None

class Experience(BaseModel):
    """Work experience entry schema"""
    title: str
    company: str
    location: str
    years: str
    description: Optional[str] = None
    descrition_list: Optional[List[str]] = None  # Note: keeping typo for compatibility
    skills: Optional[List[str]] = None
    reference: Optional[str] = None
    reference_letter_url: Optional[str] = None

class Project(BaseModel):
    """Project entry schema"""
    name: str
    role: str
    year: str
    description: str
    skills: Optional[List[str]] = None
    url: Optional[str] = None

class ProfileData(BaseModel):
    """Complete profile data schema"""
    personal_info: PersonalInfo
    summary: str
    education: List[Education]
    experience: List[Experience]
    projects: List[Project]
    skills: List[str]

class JobDescriptionRequest(BaseModel):
    """Request to fetch job description from URL"""
    url: HttpUrl = Field(..., description="URL of the job posting")

class GenerateCVRequest(BaseModel):
    """Request to generate optimized CV"""
    profile: ProfileData = Field(..., description="Candidate profile data")
    job_description: str = Field(..., description="Job description text")
    template: str = Field(default=settings.DEFAULT_TEMPLATE, description="Template type: tech, business, or modern")
    skip_validation: bool = Field(default=False, description="Skip CV validation")
    max_retries: int = Field(default=settings.MAX_RETRIES, description="Max validation retry attempts")
    model_name: str = Field(default=settings.DEFAULT_MODEL, description="LLM model to use")

class GenerateCVFromURLRequest(BaseModel):
    """Request to generate CV from job URL"""
    profile: ProfileData = Field(..., description="Candidate profile data")
    job_url: HttpUrl = Field(..., description="URL of the job posting")
    template: str = Field(default=settings.DEFAULT_TEMPLATE, description="Template type")
    skip_validation: bool = Field(default=False, description="Skip CV validation")
    max_retries: int = Field(default=settings.MAX_RETRIES, description="Max validation retry attempts")
    model_name: str = Field(default=settings.DEFAULT_MODEL, description="LLM model to use")

class CVResponse(BaseModel):
    """Response containing optimized CV data"""
    success: bool
    profile: Dict[Any, Any]
    message: Optional[str] = None

class JobInfoResponse(BaseModel):
    """Response containing parsed job information"""
    success: bool
    job_info: Dict[Any, Any]
    raw_text: Optional[str] = None

# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "online",
        "service": "Automatic CV Generator API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cv-generator-api"
    }

# ============================================================================
# Job Description Endpoints
# ============================================================================

@app.post("/api/job/fetch", response_model=JobInfoResponse, tags=["Job Description"])
async def fetch_job(request: JobDescriptionRequest):
    """
    Fetch and parse job description from URL.
    
    This endpoint:
    1. Scrapes the job posting from the provided URL
    2. Extracts relevant job information using AI
    3. Returns structured job data
    """
    try:
        # Fetch raw job description
        job_text = fetch_job_description(str(request.url))
        
        if not job_text:
            raise HTTPException(
                status_code=400, 
                detail="Failed to fetch job description from URL"
            )
        
        # Extract structured job info
        job_info = extract_relevant_job_info(job_text, settings.DEFAULT_MODEL)
        
        return JobInfoResponse(
            success=True,
            job_info=job_info,
            raw_text=job_text
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching job description: {str(e)}"
        )

@app.post("/api/job/parse", response_model=JobInfoResponse, tags=["Job Description"])
async def parse_job_text(job_text: str = Query(..., description="Raw job description text")):
    """
    Parse raw job description text into structured format.
    
    This endpoint takes raw job text and extracts structured information
    like requirements, responsibilities, and key details.
    """
    try:
        job_info = extract_relevant_job_info(job_text, settings.DEFAULT_MODEL)
        
        return JobInfoResponse(
            success=True,
            job_info=job_info,
            raw_text=job_text
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing job description: {str(e)}"
        )

# ============================================================================
# CV Extraction Endpoint
# ============================================================================

@app.post("/api/cv/extract", response_model=CVResponse, tags=["CV Extraction"])
async def extract_cv_from_pdf(
    file: UploadFile = File(..., description="PDF resume file"),
    model_name: str = Query(default=settings.DEFAULT_MODEL, description="LLM model to use")
):
    """
    Extract CV data from uploaded PDF resume.
    
    This endpoint:
    1. Accepts a PDF resume upload
    2. Extracts text and structure using AI
    3. Returns structured CV data in JSON format
    """
    # Validate file type
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Only {', '.join(settings.ALLOWED_EXTENSIONS)} files are supported"
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Extract CV data
        cv_data = extract_cv_from_pdf_smart(tmp_path, model_name)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return CVResponse(
            success=True,
            profile=cv_data,
            message="CV successfully extracted from PDF"
        )
    
    except Exception as e:
        # Clean up temp file on error
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting CV from PDF: {str(e)}"
        )

# ============================================================================
# CV Generation Endpoints
# ============================================================================

@app.post("/api/cv/generate", response_model=CVResponse, tags=["CV Generation"])
async def generate_cv(request: GenerateCVRequest):
    """
    Generate optimized CV based on job description.
    
    This endpoint:
    1. Takes your profile and a job description
    2. Optimizes your CV using AI to match the job requirements
    3. Validates the output (unless skip_validation is True)
    4. Returns the optimized CV data
    """
    try:
        # Convert Pydantic models to dict
        profile_dict = request.profile.model_dump()
        
        # Parse job description to extract structured info
        job_info = extract_relevant_job_info(
            request.job_description, 
            request.model_name
        )
        
        # Generate optimized profile
        if request.skip_validation:
            from src.llm_agent import generate_optimized_profile
            optimized_profile = generate_optimized_profile(
                profile_dict, 
                job_info, 
                request.model_name
            )
        else:
            optimized_profile = generate_optimized_profile_with_validation(
                profile=profile_dict,
                job_info=job_info,
                model_name=request.model_name,
                max_retries=request.max_retries
            )
        
        return CVResponse(
            success=True,
            profile=optimized_profile,
            message="CV successfully generated and optimized"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating CV: {str(e)}"
        )

@app.post("/api/cv/generate-from-url", response_model=CVResponse, tags=["CV Generation"])
async def generate_cv_from_url(request: GenerateCVFromURLRequest):
    """
    Generate optimized CV from job posting URL.
    
    This is a convenience endpoint that combines:
    1. Fetching the job description from URL
    2. Parsing the job requirements
    3. Generating an optimized CV
    
    All in one API call.
    """
    try:
        # Fetch job description
        job_text = fetch_job_description(str(request.job_url))
        
        if not job_text:
            raise HTTPException(
                status_code=400,
                detail="Failed to fetch job description from URL"
            )
        
        # Convert profile to dict
        profile_dict = request.profile.model_dump()
        
        # Extract job info
        job_info = extract_relevant_job_info(job_text, request.model_name)
        
        # Generate optimized profile
        if request.skip_validation:
            from src.llm_agent import generate_optimized_profile
            optimized_profile = generate_optimized_profile(
                profile_dict,
                job_info,
                request.model_name
            )
        else:
            optimized_profile = generate_optimized_profile_with_validation(
                profile=profile_dict,
                job_info=job_info,
                model_name=request.model_name,
                max_retries=request.max_retries
            )
        
        return CVResponse(
            success=True,
            profile=optimized_profile,
            message="CV successfully generated from job URL"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating CV from URL: {str(e)}"
        )

# ============================================================================
# CV Rendering Endpoints
# ============================================================================

@app.post("/api/cv/render", tags=["CV Rendering"])
async def render_cv(
    profile: ProfileData,
    template: str = Query(default=settings.DEFAULT_TEMPLATE, description="Template: tech, business, or modern"),
    output_filename: str = Query(default="cv_output.pdf", description="Output PDF filename")
):
    """
    Render CV to PDF format.
    
    Takes structured CV data and renders it to a beautiful PDF using
    the specified template (tech, business, or modern).
    
    Returns the PDF file for download.
    """
    try:
        # Validate template
        if template not in settings.AVAILABLE_TEMPLATES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid template. Available templates: {', '.join(settings.AVAILABLE_TEMPLATES)}"
            )
        
        # Convert to dict
        profile_dict = profile.model_dump()
        
        # Create output directory if it doesn't exist
        output_dir = Path(settings.OUTPUT_DIR)
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / output_filename
        
        # Render PDF
        render_cv_pdf_html(profile_dict, template=template, output_path=str(output_path))
        
        # Return PDF file
        if not output_path.exists():
            raise HTTPException(
                status_code=500,
                detail="PDF generation failed"
            )
        
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename=output_filename
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error rendering CV: {str(e)}"
        )

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Run the API server with settings from config
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD  # Auto-reload on code changes (disable in production)
    )
