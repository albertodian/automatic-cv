#!/usr/bin/env python3
"""
Startup script for the Automatic CV Generator API.

This script:
1. Checks if dependencies are installed
2. Validates environment setup
3. Starts the FastAPI server
"""

import sys
import os
import subprocess
from pathlib import Path


def check_python_version():
    """Ensure Python 3.10+"""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}")
    return True


def check_dependencies():
    """Check if required packages are installed"""
    required = ["fastapi", "uvicorn", "pydantic"]
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is NOT installed")
            missing.append(package)
    
    if missing:
        print("\n⚠️  Missing dependencies detected!")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True


def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path("../.env")
    
    if not env_path.exists():
        print("⚠️  .env file not found")
        print("   Create it with: REPLICATE_API_TOKEN=your_token")
        print("   (The API will still work, but LLM features may fail)")
        return True  # Not critical
    
    # Check if token is set
    with open(env_path) as f:
        content = f.read()
        if "REPLICATE_API_TOKEN" in content:
            print("✅ .env file found with REPLICATE_API_TOKEN")
        else:
            print("⚠️  .env file found but REPLICATE_API_TOKEN not set")
    
    return True


def check_src_modules():
    """Verify that src/ modules are accessible"""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    required_modules = [
        "src.data_loader",
        "src.job_parser",
        "src.llm_agent",
        "src.renderer"
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} is accessible")
        except ImportError as e:
            print(f"❌ {module} failed to import: {e}")
            return False
    
    return True


def start_server(host="0.0.0.0", port=8000, reload=True):
    """Start the uvicorn server"""
    print("\n" + "="*60)
    print("🚀 Starting Automatic CV Generator API")
    print("="*60)
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Reload: {reload}")
    print(f"   Working Dir: {os.getcwd()}")
    print(f"   API URL: http://localhost:{port}")
    print(f"   Docs: http://localhost:{port}/docs")
    print("="*60 + "\n")
    
    cmd = [
        "uvicorn",
        "app:app",
        "--host", host,
        "--port", str(port)
    ]
    
    if reload:
        cmd.append("--reload")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")


def main():
    """Main startup routine"""
    print("🔍 Checking system requirements...\n")
    
    # Run all checks
    checks = [
        ("Python version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment file", check_env_file),
        ("Source modules", check_src_modules),
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        if not check_func():
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ All checks passed!")
        print("="*60)
        
        # Start the server
        try:
            start_server()
        except Exception as e:
            print(f"\n❌ Failed to start server: {e}")
            sys.exit(1)
    else:
        print("❌ Some checks failed!")
        print("="*60)
        print("\n⚠️  Please fix the issues above before starting the server.")
        sys.exit(1)


if __name__ == "__main__":
    # Check if we're in the app directory
    if not Path("app.py").exists():
        print("❌ Please run this script from the app/ directory:")
        print("   cd app")
        print("   python start.py")
        sys.exit(1)
    
    main()
