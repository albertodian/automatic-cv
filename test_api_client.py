"""
Simple test client for CV Generator API
Demonstrates how to use the API endpoints
"""

import requests
import json
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_extract_job_info():
    """Test job information extraction"""
    print("\n=== Testing Job Information Extraction ===")
    
    job_text = """
    Senior Software Engineer - Remote
    
    We're looking for an experienced Python developer to join our team.
    
    Requirements:
    - 5+ years of Python experience
    - Experience with FastAPI and async programming
    - Strong knowledge of databases (PostgreSQL, MongoDB)
    - Docker and Kubernetes experience
    
    Responsibilities:
    - Design and implement RESTful APIs
    - Optimize database queries
    - Write clean, maintainable code
    """
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/job/extract",
        json={"job_text": job_text}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Job ID: {data['job_id']}")
        print(f"Extracted Info:")
        print(json.dumps(data['data'], indent=2))
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_generate_cv_from_text():
    """Test CV generation from job text"""
    print("\n=== Testing CV Generation from Text ===")
    
    job_text = """
    Python Developer Position
    
    We need a Python developer with FastAPI experience.
    Must know Docker, Git, and have 3+ years experience.
    """
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/cv/generate/text",
        json={
            "job_text": job_text,
            "template": "modern"
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        output_path = "test_cv_output.pdf"
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"✅ CV saved to: {output_path}")
        print(f"File size: {len(response.content)} bytes")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_parse_resume():
    """Test resume parsing (requires a PDF file)"""
    print("\n=== Testing Resume Parsing ===")
    
    # Check if test PDF exists
    test_pdf = "data/AUS_DianAlberto.pdf"
    if not Path(test_pdf).exists():
        print(f"⚠️  Skipping: Test PDF not found at {test_pdf}")
        return None
    
    with open(test_pdf, "rb") as f:
        files = {"file": f}
        response = requests.post(
            f"{API_BASE_URL}/api/v1/cv/parse",
            files=files
        )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Job ID: {data['job_id']}")
        print(f"Extracted Data Keys: {list(data['data'].keys())}")
        print(f"Personal Info: {data['data']['personal_info']}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_api_root():
    """Test API root endpoint"""
    print("\n=== Testing API Root ===")
    response = requests.get(f"{API_BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def main():
    """Run all tests"""
    print("=" * 60)
    print("CV Generator API - Test Suite")
    print("=" * 60)
    print(f"API Base URL: {API_BASE_URL}")
    print("\nMake sure the API server is running!")
    print("Start it with: ./start_api.sh")
    print("=" * 60)
    
    results = {}
    
    # Run tests
    results["Health Check"] = test_health_check()
    results["API Root"] = test_api_root()
    results["Job Extraction"] = test_extract_job_info()
    results["Resume Parsing"] = test_parse_resume()
    
    # CV generation test (takes longer, run last)
    print("\n⚠️  CV generation test will take 30-60 seconds...")
    user_input = input("Run CV generation test? (y/n): ")
    if user_input.lower() == 'y':
        results["CV Generation"] = test_generate_cv_from_text()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    for test_name, result in results.items():
        if result is None:
            status = "⊘ SKIPPED"
        elif result:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for r in results.values() if r is True)
    total = sum(1 for r in results.values() if r is not None)
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("Make sure the API is running at", API_BASE_URL)
        print("Start it with: ./start_api.sh")
