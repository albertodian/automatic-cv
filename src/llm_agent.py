import json
import ollama
import re
import os
import replicate
from dotenv import load_dotenv

load_dotenv()
api_token = os.getenv("REPLICATE_API_TOKEN")

if not api_token:
    raise ValueError("REPLICATE_API_TOKEN is not set in environment variables.")



def generate_optimized_profile(profile: dict, job_info: dict, model_name: str) -> dict:
    """
    Generate an ATS-optimized CV that strategically incorporates job posting keywords
    while maintaining authenticity and fitting on ONE page.
    """
    prompt = f"""
You are an expert ATS (Applicant Tracking System) optimization specialist. Your goal is to create a ONE-PAGE CV that maximizes ATS score while looking authentic.

CRITICAL PAGE LIMIT RULE:
⚠️ The CV MUST fit on ONE page when rendered. You MUST remove content to achieve this:
- Keep maximum 2-3 experiences (remove least relevant)
- Keep maximum 3-4 projects (remove least relevant)
- Each experience should have 3-4 bullets max in descrition_list
- Prioritize recent and relevant experiences over older/unrelated ones
- ⚠️ NEVER remove or modify education entries - keep ALL education exactly as provided

OPTIMIZATION STRATEGY:

1. CONTENT SELECTION (DO THIS FIRST):
   - Analyze which experiences/projects are most relevant to the job posting
   - REMOVE entire experiences/projects that are not relevant
   - For a typical job: keep 2 most relevant experiences, 3-4 most relevant projects
   - Shorten descrition_list arrays: keep only the 3-4 most impactful bullets per experience
   - Education: Keep ALL entries unchanged - do not remove or shorten

2. KEYWORD IDENTIFICATION:
   - Extract 10-15 critical technical keywords from the job posting
   - Focus on: specific tools (AWS, Docker, Kubernetes), methodologies (MLOps, Agile, CI/CD), technical skills, and domain-specific terms

3. SKILLS SECTION - RICH AND COMPREHENSIVE:
   - Goal: Create a rich, comprehensive skills array (30-40 items total)
   - Add 8-12 critical keywords from job posting
   - Keep most original skills, only remove 2-3 truly irrelevant ones
   - ⚠️ CRITICAL: Mix new keywords THROUGHOUT the array, not just at the end
   - Pattern: [original, original, NEW_KEYWORD, original, original, NEW_KEYWORD, original, NEW_KEYWORD, original, original]
   - Include variations of keywords when relevant (e.g., "AWS", "AWS Lambda", "AWS S3")
   - Example result: ["Python", "C++", "AWS", "TensorFlow", "Keras", "MLOps", "PyTorch", "Docker", "OpenCV", "ROS", "Kubernetes", "CI/CD", "REST APIs", ...]
   - The final skills array should feel comprehensive and impressive

4. EXPERIENCE SECTION - STRATEGIC ENHANCEMENT:
   - Keep only 2-3 most relevant experiences (REMOVE others completely)
   - For kept experiences, limit to 3-4 bullets in descrition_list
   - Enhance 2-3 bullets per experience with keywords naturally integrated
   - Update skills arrays with 2-4 new keywords MIXED throughout (not at end)
   - Example bullet enhancement: "Collected ~2000 robot trajectories using cloud storage (AWS S3) and designed dataset for model finetuning with MLOps pipeline"

5. PROJECTS SECTION - SELECTIVE INCLUSION:
   - Keep only 3-4 most relevant projects (REMOVE others completely)
   - Enhance 2 projects: improve descriptions with 2-3 keywords
   - Update skills arrays: add 2-4 keywords MIXED in (not appended at end)
   - Keep other projects minimal/unchanged

6. SUMMARY - CONCISE AND POWERFUL:
   - Maximum 2 sentences (not 3-4!)
   - Include 3-4 most critical keywords from job posting
   - Should be punchy and direct
   - Example: "AI Engineer specializing in machine learning deployment and cloud infrastructure (AWS). Experienced in building production-ready models with MLOps practices and cross-functional collaboration."

7. KEYWORD PLACEMENT STRATEGY:
   - Each keyword appears 2-3 times across ENTIRE CV:
     * Once in main skills array (mixed in naturally)
     * Once in experience/project bullet or description
     * Maybe once in experience/project skills array
   - Use variations: "AWS" → "cloud infrastructure (AWS)" → "AWS Lambda" → "AWS services"
   - Include related terms: If job mentions "cloud", add both "AWS" and "Cloud Computing"
   - Never cluster all new keywords together

8. WHAT TO REMOVE (PRIORITIZE THIS):
   - Remove least relevant experience(s) completely
   - Remove least relevant project(s) completely
   - Within kept experiences: remove weakest bullets, keep max 3-4
   - Older experiences (2020-2022) are often good candidates for removal unless directly relevant
   - ⚠️ DO NOT remove any education entries

9. SKILLS ARRAY RICHNESS:
   - Target: 30-40 total skills in final array
   - Include: programming languages, frameworks, tools, platforms, methodologies, domain skills
   - Mix technical and soft skills where relevant to job posting
   - Group similar items mentally but mix in array: languages scattered, tools scattered, platforms scattered
   - Examples to include if relevant: "REST APIs", "Microservices", "Agile", "Scrum", "CI/CD", "DevOps", "Data Pipelines", "Model Deployment", "A/B Testing"

INPUT DATA:

Candidate Profile:
{json.dumps(profile, indent=2, ensure_ascii=False)}

Job Posting:
{json.dumps(job_info, indent=2, ensure_ascii=False)}

OPTIMIZATION CHECKLIST:
1. ✓ Remove content to fit one page (max 2-3 experiences, 3-4 projects)
2. ✓ Keep ALL education entries unchanged
3. ✓ Summary is exactly 2 sentences with 3-4 keywords
4. ✓ Add 8-12 keywords to main skills array MIXED throughout
5. ✓ Main skills array has 30-40 items total (rich and comprehensive)
6. ✓ Enhance 4-6 bullets across kept experiences
7. ✓ Enhance 2 project descriptions
8. ✓ All new keywords are MIXED into lists, not appended at end
9. ✓ Each keyword appears 2-3 times total across CV

OUTPUT REQUIREMENTS:
Return ONLY valid JSON, no markdown, no commentary.

{{
  "personal_info": {{
    "name": "string",
    "email": "string",
    "phone": "string",
    "nationality": "string",
    "age": number,
    "linkedin": "string",
    "github": "string",
    "languages": ["array"]
  }},
  "summary": "EXACTLY 2 sentences. Must include 3-4 keywords naturally. Be concise and punchy.",
  "education": [
    {{
      "degree": "string",
      "institution": "string",
      "location": "string",
      "year": "string",
      "description": "string",
      "grade": "string"
    }}
  ],
  "experience": [
    {{
      "title": "string",
      "company": "string",
      "location": "string",
      "years": "string",
      "description": "string",
      "descrition_list": [
        "MAX 3-4 bullets per experience",
        "Enhance 2-3 bullets with keywords naturally",
        "Remove less impactful bullets"
      ],
      "skills": ["Mix", "new", "keywords", "AWS", "throughout", "not", "at", "end"],
      "reference": "string (if exists)",
      "reference_letter_url": "string (if exists)"
    }}
  ],
  "projects": [
    {{
      "name": "string",
      "role": "string",
      "year": "string",
      "description": "Enhanced for top 2 projects with keywords",
      "skills": ["Mix", "keywords", "MLOps", "naturally", "not", "appended"],
      "url": "string"
    }}
  ],
  "skills": [
    "TARGET: 15-20 items total - make it rich and comprehensive",
    "Python",
    "C++",
    "AWS",
    "TensorFlow",
    "Keras",
    "MLOps",
    "PyTorch",
    "Docker",
    "OpenCV",
    "CI/CD",
    "REST APIs",
    "Cloud Computing",
    "MIX NEW KEYWORDS THROUGHOUT - NOT ALL AT THE END",
    "Pattern: original, original, NEW, original, original, NEW, original",
    "Include variations of important keywords",
    "Should feel impressive and comprehensive"
  ]
}}

REMEMBER: 
- ONE PAGE is non-negotiable - be ruthless about removing experiences/projects
- NEVER remove education entries
- Mix keywords naturally throughout all arrays
- Summary must be exactly 2 sentences
- Skills array should be rich (30-40 items)
- Prioritize quality over quantity

BEGIN OPTIMIZATION:
"""

    output = replicate.run(
        model_name,
        input={"prompt": prompt}
    )

    content = "".join([str(x) for x in output]).strip()
    
    # Clean up potential markdown formatting
    if content.startswith("```json"):
        content = content.split("```json")[1]
    if content.startswith("```"):
        content = content.split("```")[1]
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]
    content = content.strip()

    try:
        optimized_cv = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON:\n{content}") from e

    return optimized_cv



def generate_cover_letter(profile: dict, job_text: str, model_name: str) -> str:
    """
    Generate a short tailored cover letter using Replicate model.
    """
    prompt = f"""
You are an expert in writing cover letters.

Candidate profile (JSON):
{json.dumps(profile, indent=2, ensure_ascii=False)}

Job posting:
{job_text}

Task:
Write a concise, professional cover letter (3-5 paragraphs) 
highlighting the candidate's experience and skills relevant to the job.
Do NOT invent any new facts. Return only the letter text.
"""

    output = replicate.run(
        model_name,
        input={"prompt": prompt}
    )

    content = "".join([str(x) for x in output]).strip()
    return content


def extract_relevant_job_info(job_raw_text: str, model_name: str) -> dict:
    """
    Extract and summarize a job posting into structured JSON using Replicate.
    Cleans the text, removes duplicates in keywords, and returns only valid JSON.
    All output fields are forced to English.
    """

    clean_text = re.sub(r'\s+', ' ', job_raw_text).strip()

    prompt = f"""
You are an expert at parsing job postings for ATS optimization.

TASK:
1. Parse the job posting below into structured JSON.
2. Translate ALL fields (title, company, location, summary, requirements, responsibilities, keywords)
into ENGLISH if they are not already.
3. For the field "summary": write a concise English summary (2-3 sentences) of the job posting.
4. Return ONLY valid JSON. No commentary, no explanations.

Input job posting text:
{clean_text}

STRICT Output JSON format:
{{
"title": "",
"company": "",
"location": "",
"summary": "",
"requirements": [],
"responsibilities": [],
"keywords": []
}}

Rules:
- All output MUST be in English.
- The "summary" field MUST be filled with a brief summary of the posting.
- Preserve keywords exactly but translate them to English if needed.
- Remove duplicate keywords.
- Sort keywords alphabetically.
- If some field is missing, return empty string or empty list.
- Do NOT include any extra text or comments.
"""

    output = replicate.run(
        model_name,
        input={"prompt": prompt}
    )

    content = "".join([str(x) for x in output]).strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {
            "title": "",
            "company": "",
            "location": "",
            "summary": clean_text,
            "requirements": [],
            "responsibilities": [],
            "keywords": []
        }

    # Post-processing
    if 'keywords' in parsed:
        parsed['keywords'] = sorted(list(dict.fromkeys(parsed['keywords'])))
    else:
        parsed['keywords'] = []

    for field in ['requirements', 'responsibilities']:
        if field not in parsed or not isinstance(parsed[field], list):
            parsed[field] = []

    for field in ['title', 'company', 'location', 'summary']:
        if field not in parsed or not isinstance(parsed[field], str):
            parsed[field] = ""

    return parsed

