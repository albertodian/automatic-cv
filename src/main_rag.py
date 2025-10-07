"""
RAG-Enhanced CV Generation Main Script

This script uses RAG (Retrieval-Augmented Generation) for more precise
and consistent CV generation compared to the standard approach.
"""

import sys
import os

from structure_validator import fix_cv

# Add src directory to path so modules can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import json
from utils import load_profile
from job_parser import fetch_job_description
from llm_agent import (
    extract_relevant_job_info, 
    extract_cv_from_pdf_smart, 
    generate_optimized_profile
)
from renderer import render_cv_pdf_html
from rag_system import CVRAGSystem, RAGEnhancedGenerator
from ats_optimizer import refine_cv_for_ats

#from structure_validator import fix_structure, validate_structure, print_validation_report


def main():
    parser = argparse.ArgumentParser(
        description="Generate a customized CV using RAG (Retrieval-Augmented Generation)"
    )
    parser.add_argument("--url", help="URL of the job posting")
    parser.add_argument("--resume", action="store_true", 
                       help="Extract CV data from existing PDF resume")
    parser.add_argument("--template", default="tech", 
                       help="Template type: 'tech', 'business', or 'modern'")
    parser.add_argument("--max-retries", type=int, default=2, 
                       help="Maximum validation retry attempts (default: 2)")
    parser.add_argument("--reset-rag", action="store_true",
                       help="Reset RAG database and reindex")
    args = parser.parse_args()


    # Extract CV from resume if requested
    if args.resume:
        # The user provides a PDF resume to extract from
        imported_cv = extract_cv_from_pdf_smart("data/AUS_DianAlberto.pdf", "openai/gpt-4.1-mini")
        profile, fix_messages = fix_cv(
            profile=imported_cv,
            original_profile=None,  # No original for this use case
            auto_fix=True
        )

        # Save imported profile for debugging
        os.makedirs("output/temp", exist_ok=True)
        with open("output/temp/imported_profile.json", "w") as f:
            json.dump(profile, f, indent=2)
        print("Imported profile saved to output/temp/imported_profile.json")
        
        # if fix_messages:
        #     print("Warning:", ": ".join(fix_messages))
            
    else:
        # Load candidate profile (data inserted via UI)
        print("Loading candidate profile...")
        profile = load_profile("data/profile.json")
        profile, fix_messages = fix_cv(
            profile=profile,
            original_profile=None,  # No original for this use case
            auto_fix=True
        )

    # Fetch and parse job description
    print("Fetching job description...")
    if args.url:
        # Fetch from URL (the user provides the job posting link)
        job_text_raw = fetch_job_description(args.url)
        job_text_path = os.path.join("data", "job_description.txt")
        with open(job_text_path, "w") as f:
            f.write(job_text_raw)
        print(f"Saved raw job text to {job_text_path}")
    else:
        # Load from existing file (the user pastes job description there)
        job_text_path = os.path.join("data", "job_description.txt")
        if os.path.exists(job_text_path):
            with open(job_text_path, "r") as f:
                job_text = f.read()
        else:
            job_text = ""
        
    job_info = extract_relevant_job_info(job_text, "openai/gpt-4.1-mini")
    
    job_info_path = os.path.join("output/temp", "job_info.json")
    os.makedirs(os.path.dirname(job_info_path), exist_ok=True)
    with open(job_info_path, "w") as f:
        json.dump(job_info, f, indent=2)
    print(f"Saved job info to {job_info_path}")
    
    
    # Initialize RAG system
    rag_system = CVRAGSystem()

    rag_system.reset_database()
        
    # Index profile content (now with enhanced project descriptions)
    rag_system.index_profile(profile)
        
    # Create RAG-enhanced generator
    rag_generator = RAGEnhancedGenerator(rag_system)
    
    # Generate optimized profile
    generated_profile = rag_generator.generate_optimized_profile_with_rag(
        profile=profile,
        job_info=job_info,
        llm_function=generate_optimized_profile,
        model_name="openai/gpt-4.1-mini"
    )

    # Validate and fix structure
    print("Validating and fixing CV structure...")
    final_profile, fix_messages = fix_cv(
        profile=generated_profile,
        original_profile=profile,
        auto_fix=True
    )
    
    # if fix_messages:
    #     print("Applied fixes:")
    #     for msg in fix_messages:
    #         print(f"  {msg}")

    # Apply ATS iterative refinement to achieve 90%+ score
    final_profile, ats_result, iterations = refine_cv_for_ats(
        profile=final_profile,
        job_keywords=job_info.get('keywords', []),
        model_name="openai/gpt-4.1-mini",
        max_iterations=3,
        target_score=90.0,
        min_improvement=5.0
    )

    # Save final validated version
    output_filename = "optimized_profile.json"
    optimized_profile_path = os.path.join("output/temp", output_filename)
    with open(optimized_profile_path, "w") as f:
        json.dump(final_profile, f, indent=2)

    # Save ATS report
    ats_report_path = os.path.join("output/temp", "ats_report.json")
    with open(ats_report_path, "w") as f:
        json.dump(ats_result, f, indent=2)

    print(f"\n Saved ATS-optimized profile to {optimized_profile_path}")
    print(f"\n Saved ATS report to {ats_report_path}")
        
    # Render PDF
    render_cv_pdf_html(final_profile, template=args.template, output_filename="cv_output.pdf")
    
    print("CV Generation complete!")
    print(f"Output: output/cv_output.pdf")


if __name__ == "__main__":
    main()
