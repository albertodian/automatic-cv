import argparse
from data_loader import load_profile
from job_parser import fetch_job_description
from llm_agent import generate_optimized_profile, generate_cover_letter, extract_relevant_job_info, extract_cv_from_pdf_smart, save_cv_to_json
from renderer import render_cv_pdf_html, render_cover_letter_pdf
from cv_validator import validate_cv
import os
import json

def main():
    parser = argparse.ArgumentParser(description="Generate a customized CV (and optional cover letter)")
    parser.add_argument("--url", help="URL of the job posting")
    parser.add_argument("--resume", action="store_true", help="Extract CV data from existing PDF resume")
    #parser.add_argument("--model", default="llama3.1:8b", help="Ollama model name")
    parser.add_argument("--template", required=True, default="tech", help="Template type: 'tech', 'business', or 'modern'")
    parser.add_argument("--skip-validation", action="store_true", help="Skip CV validation and auto-correction")
    args = parser.parse_args()

    if args.resume:
        cv_data = extract_cv_from_pdf_smart("data/AUS_DianAlberto.pdf", "openai/gpt-4.1-mini")
        save_cv_to_json(cv_data, "data/profile_fetched.json")
        print("Extracted CV data from resume and saved to data/profile_fetched.json")
    

    # Load candidate profile
    print("Loading candidate profile...")
    profile = load_profile("data/profile_fetched.json")

    # Fetch and parse job description
    print("Fetching job description...")

    # If URL is provided, fetch job description and save to file
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
    with open(job_info_path, "w") as f:
        json.dump(job_info, f, indent=2)
    print(f"Saved job info to {job_info_path}")

    # Generate optimized CV profile
    print("Generating optimized CV profile...")
    optimized_profile_json = generate_optimized_profile(profile, job_info, "openai/gpt-4.1-mini")
    
    if not args.skip_validation:
        print("\n🔍 Validating and auto-correcting CV...")
        corrected_profile_json, validation_issues = validate_cv(
            cv_data=optimized_profile_json,
            job_info=job_info,
            template_path="templates/cv_template.html"
        )
        
        if validation_issues:
            print(f"📋 Found and addressed {len(validation_issues)} issues:")
            for issue in validation_issues[-5:]:  # Show last 5 issues
                print(f"   • {issue}")
            
            # Save both versions for comparison
            optimized_profile_path = os.path.join("output/temp", "optimized_profile_raw.json")
            with open(optimized_profile_path, "w") as f:
                json.dump(optimized_profile_json, f, indent=2)
            print(f"Saved raw optimized profile to {optimized_profile_path}")
            
            corrected_profile_path = os.path.join("output/temp", "optimized_profile.json")
            with open(corrected_profile_path, "w") as f:
                json.dump(corrected_profile_json, f, indent=2)
            print(f"Saved corrected profile to {corrected_profile_path}")
            
            # Use corrected version for rendering
            final_profile = corrected_profile_json
            print("✅ Using corrected version for final CV")
            
        else:
            print("✅ No issues found - CV passes all validations!")
            optimized_profile_path = os.path.join("output/temp", "optimized_profile.json")
            with open(optimized_profile_path, "w") as f:
                json.dump(optimized_profile_json, f, indent=2)
            print(f"Saved optimized profile to {optimized_profile_path}")
            
            # Use original version
            final_profile = optimized_profile_json
    else:
        print("⏭️ Skipping validation (--skip-validation flag used)")
        optimized_profile_path = os.path.join("output/temp", "optimized_profile.json")
        with open(optimized_profile_path, "w") as f:
            json.dump(optimized_profile_json, f, indent=2)
        print(f"Saved optimized profile to {optimized_profile_path}")
        final_profile = optimized_profile_json
    
    render_cv_pdf_html(final_profile)

if __name__ == "__main__":
    main()
