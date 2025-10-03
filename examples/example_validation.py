#!/usr/bin/env python3
"""
Example script demonstrating the CV validation system.

This shows how the validator can catch and fix common issues like:
- Content that's too long for one page
- Missing required fields
- Too many experiences/projects
- Inconsistent formatting
"""

import sys
import os
import json
from pathlib import Path

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from cv_validator import validate_cv


def create_problematic_cv():
    """Create a CV with several issues for demonstration."""
    return {
        "personal_info": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "nationality": "",
            "age": 0,
            "linkedin": "",
            "github": "",
            "languages": []
        },
        "summary": "",  # Missing summary
        "education": [
            {
                "degree": "Bachelor of Computer Science",
                "institution": "University A",
                "location": "City A",
                "year": "2018-2022",  # Wrong format
                "description": "",
                "grade": ""
            }
        ],
        "experience": [  # Too many experiences (5 > 3)
            {
                "title": "Senior Software Engineer",
                "company": "Company A",
                "location": "City A", 
                "years": "2022-2024",
                "description": "Led development team",
                "descrition_list": [
                    "Developed applications",
                    "Managed team of 5",
                    "Implemented CI/CD",
                    "Code reviews",
                    "Architecture decisions",
                    "Performance optimization"  # Too many bullets (6 > 4)
                ],
                "skills": ["Python", "JavaScript"],
                "reference": "",
                "reference_letter_url": ""
            },
            {
                "title": "Software Engineer",
                "company": "Company B", 
                "location": "City B",
                "years": "2020-2022",
                "description": "Backend development",
                "descrition_list": ["Built APIs", "Database design"],
                "skills": ["Python", "SQL"],
                "reference": "",
                "reference_letter_url": ""
            },
            {
                "title": "Junior Developer",
                "company": "Company C",
                "location": "City C",
                "years": "2019-2020", 
                "description": "Frontend work",
                "descrition_list": ["React components", "UI design"],
                "skills": ["React", "CSS"],
                "reference": "",
                "reference_letter_url": ""
            },
            {
                "title": "Intern",
                "company": "Company D",
                "location": "City D",
                "years": "2018-2019",
                "description": "Learning and support",
                "descrition_list": ["Bug fixes", "Testing"],
                "skills": ["JavaScript"],
                "reference": "",
                "reference_letter_url": ""
            },
            {
                "title": "Freelancer",
                "company": "Self-employed",
                "location": "Remote",
                "years": "2017-2018",
                "description": "Various projects",
                "descrition_list": ["Small websites", "TODO: add more details"],  # Placeholder text
                "skills": ["HTML", "CSS"],
                "reference": "",
                "reference_letter_url": ""
            }
        ],
        "projects": [  # Too many projects (6 > 4)
            {"name": "Project A", "role": "Lead", "year": "2024", "description": "Web app", "skills": ["React"], "url": ""},
            {"name": "Project B", "role": "Dev", "year": "2023", "description": "Mobile app", "skills": ["React Native"], "url": ""},
            {"name": "Project C", "role": "Dev", "year": "2023", "description": "API service", "skills": ["Python"], "url": ""},
            {"name": "Project D", "role": "Dev", "year": "2022", "description": "Dashboard", "skills": ["Vue.js"], "url": ""},
            {"name": "Project E", "role": "Dev", "year": "2022", "description": "CLI tool", "skills": ["Python"], "url": ""},
            {"name": "Project F", "role": "Dev", "year": "2021", "description": "TBD - need to write", "skills": ["Java"], "url": ""}  # Placeholder
        ],
        "skills": [  # Too many skills (35 > 25)
            "Python", "JavaScript", "React", "Vue.js", "Node.js", "Express", "FastAPI", "Django",
            "PostgreSQL", "MongoDB", "Redis", "Docker", "Kubernetes", "AWS", "GCP", "Azure",
            "Git", "CI/CD", "Jenkins", "GitHub Actions", "Linux", "Bash", "HTML", "CSS", 
            "SASS", "TypeScript", "GraphQL", "REST APIs", "Microservices", "TCP/IP", "HTTP",
            "OAuth", "JWT", "Agile", "Scrum"
        ]
    }


def create_sample_job_info():
    """Create sample job information for testing."""
    return {
        "title": "Senior Python Developer",
        "company": "TechCorp",
        "location": "San Francisco, CA",
        "summary": "Looking for experienced Python developer with cloud experience",
        "requirements": ["Python", "AWS", "Docker", "Kubernetes"],
        "responsibilities": ["Build scalable systems", "Lead team"],
        "keywords": ["Python", "AWS", "Docker", "Kubernetes", "FastAPI", "PostgreSQL", "Redis"]
    }


def main():
    """Demonstrate the CV validation system."""
    print("🔍 CV Validation System Demo")
    print("=" * 40)
    
    # Create problematic CV
    print("\n1. Creating a CV with multiple issues...")
    problematic_cv = create_problematic_cv()
    
    print("   Issues in this CV:")
    print("   • Missing summary")
    print("   • Wrong date format (2018-2022 instead of Sep 2018 - Jun 2022)")
    print("   • Too many experiences (5, should be ≤3)")
    print("   • Too many bullets in first experience (6, should be ≤4)")
    print("   • Too many projects (6, should be ≤4)")
    print("   • Too many skills (35, should be ~25)")
    print("   • Placeholder text in descriptions")
    print("   • Content likely exceeds 1 page")
    
    # Create job info
    job_info = create_sample_job_info()
    
    # Run validation
    print("\n2. Running validation and auto-correction...")
    print("   This may take a moment...")
    
    try:
        corrected_cv, issues = validate_cv(
            cv_data=problematic_cv,
            job_info=job_info,
            template_path="templates/cv_template.html"
        )
        
        print(f"\n3. Validation Results:")
        print(f"   📋 Total issues found: {len(issues)}")
        
        if issues:
            print("\n   Issues detected and fixed:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i:2d}. {issue}")
        
        print(f"\n4. Comparison:")
        print(f"   Original experiences: {len(problematic_cv.get('experience', []))}")
        print(f"   Corrected experiences: {len(corrected_cv.get('experience', []))}")
        
        print(f"   Original projects: {len(problematic_cv.get('projects', []))}")
        print(f"   Corrected projects: {len(corrected_cv.get('projects', []))}")
        
        print(f"   Original skills: {len(problematic_cv.get('skills', []))}")
        print(f"   Corrected skills: {len(corrected_cv.get('skills', []))}")
        
        # Show first experience bullets
        orig_bullets = len(problematic_cv['experience'][0].get('descrition_list', []))
        corr_bullets = len(corrected_cv['experience'][0].get('descrition_list', []))
        print(f"   First experience bullets: {orig_bullets} → {corr_bullets}")
        
        print(f"\n5. Sample corrected experience:")
        if corrected_cv.get('experience'):
            exp = corrected_cv['experience'][0]
            print(f"   Title: {exp.get('title')}")
            print(f"   Company: {exp.get('company')}")
            print(f"   Bullets: {len(exp.get('descrition_list', []))}")
            for bullet in exp.get('descrition_list', [])[:2]:
                print(f"   • {bullet}")
            if len(exp.get('descrition_list', [])) > 2:
                print(f"   • ... (+{len(exp.get('descrition_list', [])) - 2} more)")
        
        # Save results for inspection
        output_dir = Path("output/temp")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "validation_demo_original.json", 'w') as f:
            json.dump(problematic_cv, f, indent=2)
        
        with open(output_dir / "validation_demo_corrected.json", 'w') as f:
            json.dump(corrected_cv, f, indent=2)
        
        print(f"\n6. Files saved:")
        print(f"   📄 Original CV: output/temp/validation_demo_original.json")
        print(f"   📄 Corrected CV: output/temp/validation_demo_corrected.json")
        print(f"\n✅ Validation demo completed successfully!")
        
        print(f"\n💡 Next steps:")
        print(f"   1. Compare the JSON files to see what changed")
        print(f"   2. Run the main CV generator: python src/main.py --url <job_url>")
        print(f"   3. The validator will automatically run unless you use --skip-validation")
        
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        print(f"\nTroubleshooting:")
        print(f"   • Make sure you're in the automatic-cv directory")
        print(f"   • Check that templates/cv_template.html exists")
        print(f"   • For full page counting, install: pip install weasyprint")


if __name__ == "__main__":
    main()