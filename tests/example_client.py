"""
Example client for the Automatic CV Generator API.

This script demonstrates how to use the API endpoints.
"""

import requests
import json
from pathlib import Path


# Base URL of your API
BASE_URL = "http://localhost:8000"


def check_health():
    """Check if the API is running"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:", response.json())
    return response.status_code == 200


def fetch_job_from_url(job_url: str):
    """Fetch and parse job description from URL"""
    response = requests.post(
        f"{BASE_URL}/api/job/fetch",
        json={"url": job_url}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Job fetched successfully!")
        print(f"Job Info: {json.dumps(data['job_info'], indent=2)}")
        return data['job_info']
    else:
        print(f"❌ Error: {response.json()}")
        return None


def parse_job_text(job_text: str):
    """Parse raw job description text"""
    response = requests.post(
        f"{BASE_URL}/api/job/parse",
        params={"job_text": job_text}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Job parsed successfully!")
        return data['job_info']
    else:
        print(f"❌ Error: {response.json()}")
        return None


def extract_cv_from_pdf(pdf_path: str):
    """Extract CV data from PDF file"""
    with open(pdf_path, 'rb') as f:
        files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
        response = requests.post(
            f"{BASE_URL}/api/cv/extract",
            files=files
        )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ CV extracted successfully!")
        return data['profile']
    else:
        print(f"❌ Error: {response.json()}")
        return None


def generate_cv(profile_data: dict, job_description: str, template: str = "tech"):
    """Generate optimized CV from profile and job description"""
    request_data = {
        "profile": profile_data,
        "job_description": job_description,
        "template": template,
        "skip_validation": False,
        "max_retries": 2
    }
    
    response = requests.post(
        f"{BASE_URL}/api/cv/generate",
        json=request_data
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ CV generated successfully!")
        return data['profile']
    else:
        print(f"❌ Error: {response.json()}")
        return None


def generate_cv_from_url(profile_data: dict, job_url: str, template: str = "tech"):
    """Generate optimized CV from profile and job URL (all-in-one)"""
    request_data = {
        "profile": profile_data,
        "job_url": job_url,
        "template": template,
        "skip_validation": False,
        "max_retries": 2
    }
    
    response = requests.post(
        f"{BASE_URL}/api/cv/generate-from-url",
        json=request_data
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ CV generated successfully!")
        return data['profile']
    else:
        print(f"❌ Error: {response.json()}")
        return None


def render_cv_to_pdf(profile_data: dict, template: str = "tech", output_filename: str = "cv_output.pdf"):
    """Render CV to PDF and download it"""
    response = requests.post(
        f"{BASE_URL}/api/cv/render",
        json=profile_data,
        params={
            "template": template,
            "output_filename": output_filename
        }
    )
    
    if response.status_code == 200:
        # Save the PDF
        with open(output_filename, 'wb') as f:
            f.write(response.content)
        print(f"✅ CV rendered successfully! Saved as {output_filename}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


# ============================================================================
# Example Usage
# ============================================================================

def example_full_workflow():
    """Complete example: Generate CV from job URL and render to PDF"""
    
    print("="*60)
    print("AUTOMATIC CV GENERATOR - API CLIENT EXAMPLE")
    print("="*60)
    
    # 1. Check API health
    print("\n1. Checking API health...")
    if not check_health():
        print("API is not running! Please start it first.")
        return
    
    # 2. Load your profile (or extract from PDF)
    print("\n2. Loading profile...")
    profile_path = "../data/profile.json"
    
    if Path(profile_path).exists():
        with open(profile_path, 'r') as f:
            profile = json.load(f)
        print("✅ Profile loaded from JSON")
    else:
        print("❌ Profile not found. Using example data...")
        # You could also extract from PDF here:
        # profile = extract_cv_from_pdf("path/to/resume.pdf")
        return
    
    # 3. Generate CV from job URL
    print("\n3. Generating optimized CV...")
    job_url = "https://example.com/job-posting"  # Replace with actual URL
    
    # Option A: All-in-one (fetch job + generate CV)
    # optimized_cv = generate_cv_from_url(profile, job_url, template="tech")
    
    # Option B: Step by step
    # Step 3a: Fetch job
    job_text = """
    Software Engineer Position
    
    Requirements:
    - 3+ years Python experience
    - Experience with FastAPI and REST APIs
    - Knowledge of Docker and Kubernetes
    - Strong problem-solving skills
    
    Responsibilities:
    - Design and implement backend services
    - Write clean, maintainable code
    - Collaborate with cross-functional teams
    """
    
    # Step 3b: Generate CV
    optimized_cv = generate_cv(profile, job_text, template="tech")
    
    if not optimized_cv:
        print("Failed to generate CV")
        return
    
    # 4. Render to PDF
    print("\n4. Rendering CV to PDF...")
    render_cv_to_pdf(optimized_cv, template="tech", output_filename="my_optimized_cv.pdf")
    
    # 5. Save optimized CV JSON (optional)
    print("\n5. Saving optimized CV data...")
    with open("optimized_cv.json", 'w') as f:
        json.dump(optimized_cv, f, indent=2)
    print("✅ Saved to optimized_cv.json")
    
    print("\n" + "="*60)
    print("WORKFLOW COMPLETE!")
    print("="*60)


def example_extract_cv():
    """Example: Extract CV from PDF"""
    print("\n📄 Extracting CV from PDF...")
    pdf_path = "../data/AUS_DianAlberto.pdf"
    
    if Path(pdf_path).exists():
        cv_data = extract_cv_from_pdf(pdf_path)
        
        if cv_data:
            # Save extracted data
            with open("extracted_cv.json", 'w') as f:
                json.dump(cv_data, f, indent=2)
            print("✅ Saved extracted CV to extracted_cv.json")
    else:
        print(f"❌ PDF not found at {pdf_path}")


if __name__ == "__main__":
    # Run the full workflow example
    example_full_workflow()
    
    # Or try individual functions:
    # example_extract_cv()
    # check_health()
    # etc.
