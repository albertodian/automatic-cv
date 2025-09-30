import argparse
from data_loader import load_profile
from job_parser import fetch_job_description
from llm_agent import generate_optimized_profile, generate_cover_letter, extract_relevant_job_info
from renderer import render_cv_pdf_html, render_cover_letter_pdf
import os
import json

def main():
    parser = argparse.ArgumentParser(description="Generate a customized CV (and optional cover letter)")
    parser.add_argument("--url", help="URL of the job posting")
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama model name")
    parser.add_argument("--cover", action="store_true", help="Also generate cover letter")
    args = parser.parse_args()

    # Load candidate profile
    print("Loading candidate profile...")
    profile = load_profile("data/profile.json")

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
        
    job_info = extract_relevant_job_info(job_text, model_name=args.model)
    
    # job_info_path = os.path.join("output/temp", "job_info.json")
    # with open(job_info_path, "w") as f:
    #     json.dump(job_info, f, indent=2)
    # print(f"Saved job info to {job_info_path}")

    # Generate optimized CV profile
    print("Generating optimized CV profile...")
    optimized_profile_json, text_explanation = generate_optimized_profile(profile, job_info, model_name=args.model)
    
    # optimized_profile_path = os.path.join("output", "optimized_profile.json")
    # with open(optimized_profile_path, "w") as f:
    #     json.dump(optimized_profile_json, f, indent=2)
    # print(f"Saved optimized profile to {optimized_profile_path}")
    
    render_cv_pdf_html(optimized_profile_json)
    print(text_explanation)

    # Generate cover letter if requested
    if args.cover:
        cover_text = generate_cover_letter(profile, job_info, model_name=args.model)
        render_cover_letter_pdf(cover_text, profile, {"title": "Hiring Team"})

if __name__ == "__main__":
    main()
