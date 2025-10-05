"""
RAG-Enhanced CV Generation Main Script

This script uses RAG (Retrieval-Augmented Generation) for more precise
and consistent CV generation compared to the standard approach.
"""

import sys
import os

# Add src directory to path so modules can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import json
from data_loader import load_profile
from job_parser import fetch_job_description
from llm_agent import (
    generate_optimized_profile_with_validation,
    extract_relevant_job_info, 
    extract_cv_from_pdf_smart, 
    save_cv_to_json,
    generate_optimized_profile
)
from renderer import render_cv_pdf_html, render_cover_letter_pdf
from rag_system import CVRAGSystem, RAGEnhancedGenerator
from ats_optimizer import (
    optimize_profile_for_ats,
    predict_ats_score,
    validate_ats_structure
)
from ats_refiner import refine_cv_for_ats, get_ats_summary
from structure_validator import fix_structure, validate_structure, print_validation_report


def main():
    parser = argparse.ArgumentParser(
        description="Generate a customized CV using RAG (Retrieval-Augmented Generation)"
    )
    parser.add_argument("--url", help="URL of the job posting")
    parser.add_argument("--resume", action="store_true", 
                       help="Extract CV data from existing PDF resume")
    parser.add_argument("--template", default="tech", 
                       help="Template type: 'tech', 'business', or 'modern'")
    parser.add_argument("--skip-validation", action="store_true", 
                       help="Skip CV validation and auto-correction")
    parser.add_argument("--max-retries", type=int, default=2, 
                       help="Maximum validation retry attempts (default: 2)")
    parser.add_argument("--no-rag", action="store_true",
                       help="Disable RAG system (use standard generation)")
    parser.add_argument("--reset-rag", action="store_true",
                       help="Reset RAG database and reindex")
    parser.add_argument("--embedding-model", default="all-MiniLM-L6-v2",
                       help="Sentence transformer model for embeddings")
    args = parser.parse_args()



    # Extract CV from resume if requested
    if args.resume:
        cv_data = extract_cv_from_pdf_smart("data/AUS_DianAlberto.pdf", "openai/gpt-4.1-mini")
        save_cv_to_json(cv_data, "data/profile_fetched.json")
        print("Extracted CV data from resume and saved to data/profile_fetched.json")

    # Load candidate profile
    print("Loading candidate profile...")
    profile = load_profile("data/profile.json")

    # Fetch and parse job description
    print("Fetching job description...")
    if args.url:
        job_text_raw = fetch_job_description(args.url)
        job_text_path = os.path.join("data", "job_description.txt")
        with open(job_text_path, "w") as f:
            f.write(job_text_raw)
        print(f"Saved raw job text to {job_text_path}")
    else:
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

    # Initialize RAG system (unless disabled)
    if not args.no_rag:
        print("\n" + "="*60)
        print("INITIALIZING RAG SYSTEM")
        print("="*60)
        
        rag_system = CVRAGSystem(
            model_name=args.embedding_model,
            persist_directory="./data/chroma_db",
            collection_name="cv_content"
        )
        
        rag_system.reset_database()
        
        # Index profile content
        rag_system.index_profile(profile)
        
        # Create RAG-enhanced generator
        rag_generator = RAGEnhancedGenerator(rag_system)
        
        print("\n" + "="*60)
        print("GENERATING OPTIMIZED CV WITH RAG")
        print("="*60)
    
    # Generate optimized profile
    if not args.skip_validation:
        if not args.no_rag:
            # RAG-enhanced generation with validation
            final_profile = rag_generator.generate_optimized_profile_with_rag(
                profile=profile,
                job_info=job_info,
                llm_function=lambda p, j, m: generate_optimized_profile_with_validation(
                    p, j, m, max_retries=args.max_retries
                ),
                model_name="openai/gpt-4.1-mini"
            )
        else:
            # Standard generation with validation
            print("Using standard generation (RAG disabled)")
            final_profile = generate_optimized_profile_with_validation(
                profile=profile,
                job_info=job_info,
                model_name="openai/gpt-4.1-mini",
                max_retries=args.max_retries
            )
        
        # Validate structure first
        print("\n" + "="*60)
        print("🎯 VALIDATING CV STRUCTURE")
        print("="*60)
        structure_warnings = validate_ats_structure(final_profile)
        for warning in structure_warnings:
            print(f"   {warning}")
        
        # Apply ATS iterative refinement to achieve 90%+ score
        final_profile, ats_result, iterations = refine_cv_for_ats(
            profile=final_profile,
            job_keywords=job_info.get('keywords', []),
            model_name="openai/gpt-4.1-mini",
            max_iterations=3,
            target_score=90.0,
            min_improvement=5.0
        )
        
        # Show final ATS summary
        print(get_ats_summary(ats_result))
        
        # CRITICAL: Fix structure one final time before saving
        print("\n🔧 Final structure validation and fixing...")
        final_profile = fix_structure(final_profile)
        print_validation_report(final_profile)
        
        # Save final validated version
        output_filename = "optimized_profile_rag.json" if not args.no_rag else "optimized_profile.json"
        optimized_profile_path = os.path.join("output/temp", output_filename)
        with open(optimized_profile_path, "w") as f:
            json.dump(final_profile, f, indent=2)
        
        # Save ATS report
        ats_report_path = os.path.join("output/temp", "ats_report.json")
        with open(ats_report_path, "w") as f:
            json.dump(ats_result, f, indent=2)
        
        print(f"\n✅ Saved ATS-optimized profile to {optimized_profile_path}")
        print(f"✅ Saved ATS report to {ats_report_path}")
        
    else:
        # Skip validation (old behavior)
        print("Skipping validation (--skip-validation flag used)")
        
        if not args.no_rag:
            final_profile = rag_generator.generate_optimized_profile_with_rag(
                profile=profile,
                job_info=job_info,
                llm_function=generate_optimized_profile,
                model_name="openai/gpt-4.1-mini"
            )
        else:
            final_profile = generate_optimized_profile(profile, job_info, "openai/gpt-4.1-mini")
        
        # Apply ATS iterative refinement even without validation
        final_profile, ats_result, iterations = refine_cv_for_ats(
            profile=final_profile,
            job_keywords=job_info.get('keywords', []),
            model_name="openai/gpt-4.1-mini",
            max_iterations=3,
            target_score=90.0,
            min_improvement=5.0
        )
        
        # Show final ATS summary
        print(get_ats_summary(ats_result))
        
        # CRITICAL: Fix structure one final time before saving
        print("\n🔧 Final structure validation and fixing...")
        final_profile = fix_structure(final_profile)
        print_validation_report(final_profile)
        
        output_filename = "optimized_profile_rag.json" if not args.no_rag else "optimized_profile.json"
        optimized_profile_path = os.path.join("output/temp", output_filename)
        with open(optimized_profile_path, "w") as f:
            json.dump(final_profile, f, indent=2)
        
        ats_report_path = os.path.join("output/temp", "ats_report.json")
        with open(ats_report_path, "w") as f:
            json.dump(ats_result, f, indent=2)
        
        print(f"\n✅ Saved ATS-optimized profile to {optimized_profile_path}")
        print(f"✅ Saved ATS report to {ats_report_path}")
    
    # Render PDF
    output_pdf = "cv_output_rag.pdf" if not args.no_rag else "cv_output.pdf"
    render_cv_pdf_html(final_profile, template=args.template, output_filename=output_pdf)
    
    print("\n" + "="*60)
    print("✅ CV GENERATION COMPLETE!")
    print("="*60)
    if not args.no_rag:
        print("🚀 RAG-enhanced generation used for maximum precision")
    print(f"📄 Output: output/{output_pdf}")


if __name__ == "__main__":
    main()
