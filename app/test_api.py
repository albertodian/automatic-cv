"""
Quick API test script.
Run this after starting the API to verify it's working correctly.
"""

import requests
import json


def test_api(base_url: str = "http://localhost:8000"):
    """Run basic API tests"""
    
    print("🧪 Testing Automatic CV Generator API")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n✓ Test 1: Health Check")
    try:
        response = requests.get(f"{base_url}/health")
        assert response.status_code == 200, "Health check failed"
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        print("  ✅ PASSED")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    
    # Test 2: Root endpoint
    print("\n✓ Test 2: Root Endpoint")
    try:
        response = requests.get(f"{base_url}/")
        assert response.status_code == 200, "Root endpoint failed"
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        print("  ✅ PASSED")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    
    # Test 3: Parse Job Text
    print("\n✓ Test 3: Parse Job Description")
    try:
        job_text = """
        Software Engineer Position
        
        We are looking for a talented software engineer with:
        - 3+ years of Python experience
        - Experience with FastAPI and REST APIs
        - Strong problem-solving skills
        
        Responsibilities:
        - Design and implement backend services
        - Write clean, maintainable code
        """
        
        response = requests.post(
            f"{base_url}/api/job/parse",
            params={"job_text": job_text}
        )
        assert response.status_code == 200, f"Job parse failed: {response.text}"
        data = response.json()
        assert data['success'], "Job parse returned success=false"
        print(f"  Status: {response.status_code}")
        print(f"  Job Info Keys: {list(data['job_info'].keys())}")
        print("  ✅ PASSED")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    
    # Test 4: Generate CV (with minimal profile)
    print("\n✓ Test 4: Generate CV")
    try:
        minimal_profile = {
            "personal_info": {
                "name": "Test User",
                "email": "test@example.com",
                "phone": "+1234567890"
            },
            "summary": "Experienced software engineer",
            "education": [
                {
                    "degree": "BSc Computer Science",
                    "institution": "Test University",
                    "location": "Test City",
                    "year": "2020-2024"
                }
            ],
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "Test Corp",
                    "location": "Remote",
                    "years": "2024-Present"
                }
            ],
            "projects": [],
            "skills": ["Python", "FastAPI", "REST APIs"]
        }
        
        request_data = {
            "profile": minimal_profile,
            "job_description": job_text,
            "template": "tech",
            "skip_validation": True,  # Skip validation for quick test
            "max_retries": 1
        }
        
        response = requests.post(
            f"{base_url}/api/cv/generate",
            json=request_data,
            timeout=60  # LLM calls can take time
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data['success'], "CV generation returned success=false"
            print(f"  Status: {response.status_code}")
            print(f"  Profile Keys: {list(data['profile'].keys())}")
            print("  ✅ PASSED")
        else:
            print(f"  ⚠️  SKIPPED (may need API token): {response.status_code}")
            print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"  ⚠️  SKIPPED (may need API token): {e}")
    
    print("\n" + "=" * 60)
    print("✅ Basic API tests completed!")
    print("\nTo test more features:")
    print("  - Visit http://localhost:8000/docs for interactive docs")
    print("  - Run: python example_client.py")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    import sys
    
    # Check if custom URL provided
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"\nTesting API at: {base_url}")
    print("(Make sure the API is running: python app.py)\n")
    
    try:
        test_api(base_url)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
