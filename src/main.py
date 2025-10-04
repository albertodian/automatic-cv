import argparse
from data_loader import load_profile
from job_parser import fetch_job_description
from llm_agent import (
    generate_optimized_profile_with_validation,
    extract_relevant_job_info, 
    extract_cv_from_pdf_smart, 
    save_cv_to_json
)
from renderer import render_cv_pdf_html, render_cover_letter_pdf
import os
import json

def main():
    parser = argparse.ArgumentParser(description="Generate a customized CV (and optional cover letter)")
    parser.add_argument("--url", help="URL of the job posting")
    parser.add_argument("--resume", action="store_true", help="Extract CV data from existing PDF resume")
    parser.add_argument("--template", default="tech", help="Template type: 'tech', 'business', or 'modern'")
    parser.add_argument("--skip-validation", action="store_true", help="Skip CV validation and auto-correction")
    parser.add_argument("--max-retries", type=int, default=2, help="Maximum validation retry attempts (default: 2)")
    args = parser.parse_args()

    # Extract CV from resume if requested
    if args.resume:
        cv_data = extract_cv_from_pdf_smart("data/AUS_DianAlberto.pdf", "openai/gpt-4.1-mini")
        save_cv_to_json(cv_data, "data/profile_fetched.json")
        print("Extracted CV data from resume and saved to data/profile_fetched.json")
        return

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

    
    if not args.skip_validation:
        # Use validation with auto-correction
        final_profile = generate_optimized_profile_with_validation(
            profile=profile,
            job_info=job_info,
            model_name="openai/gpt-4.1-mini",
            max_retries=args.max_retries
        )
        
        # Save final validated version
        optimized_profile_path = os.path.join("output/temp", "optimized_profile.json")
        with open(optimized_profile_path, "w") as f:
            json.dump(final_profile, f, indent=2)
        print(f"\nSaved validated profile to {optimized_profile_path}")
        
    else:
        # Skip validation (old behavior)
        from llm_agent import generate_optimized_profile
        print("Skipping validation (--skip-validation flag used)")
        final_profile = generate_optimized_profile(profile, job_info, "openai/gpt-4.1-mini")
        
        optimized_profile_path = os.path.join("output/temp", "optimized_profile.json")
        with open(optimized_profile_path, "w") as f:
            json.dump(final_profile, f, indent=2)
        print(f"Saved optimized profile to {optimized_profile_path}")
    
    render_cv_pdf_html(final_profile, template=args.template)
    print("\nCV generation complete!")

if __name__ == "__main__":
    main()
