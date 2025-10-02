import json
import re
import os
import replicate
import PyPDF2
import pdfplumber
import fitz
import pytesseract
from pdf2image import convert_from_path
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

1. CONTENT SELECTION - SYSTEMATIC RELEVANCE SCORING (DO THIS FIRST):
   
   A. EXPERIENCE RELEVANCE SCORING:
   For each experience, assign a relevance score (0-10) based on:
   - Technical alignment: Does it use similar technologies/skills as the job? (0-4 points)
   - Domain alignment: Is it in a similar field/industry? (0-3 points)
   - Recency: How recent is it? (0-2 points: 2024-2025=2pts, 2022-2023=1pt, before 2022=0pts)
   - Seniority/Impact: Does the role level match the job posting? (0-1 point)
   
   Scoring examples:
   - AI Engineer at tech company using ML/Python for recent work = 9-10 points (KEEP)
   - Software intern at related company 2 years ago = 5-6 points (MAYBE)
   - Non-technical mentor role from 2020 = 1-3 points (REMOVE)
   
   RULE: Keep the top 2-3 experiences with highest scores. Always prefer recent (2023+) technical roles.
   
   B. PROJECT RELEVANCE SCORING:
   For each project, assign a relevance score (0-10) based on:
   - Technology overlap: Does it use tools/frameworks mentioned in job posting? (0-5 points)
   - Problem domain: Does it solve similar problems as the job? (0-3 points)
   - Complexity/Impact: Is it a substantial, impressive project? (0-2 points)
   
   Scoring examples:
   - ML project using same stack as job posting = 9-10 points (KEEP)
   - Web app with some relevant tech = 5-6 points (MAYBE)
   - Unrelated creative/design project = 2-4 points (REMOVE)
   
   RULE: Keep the top 3-4 projects with highest scores. Prioritize technical projects over creative ones unless creativity is in job posting.
   
   C. SELECTION LOGIC:
   - Score ALL experiences and projects systematically
   - Sort by score (highest first)
   - Keep top 2-3 experiences (minimum 2, maximum 3)
   - Keep top 3-4 projects (minimum 3, maximum 4)
   - Document your reasoning mentally: "Keeping X because [technical alignment + recency], removing Y because [low relevance + old]"

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
   - Keep only 2-3 most relevant experiences based on scoring (REMOVE others completely)
   - For kept experiences, limit to 3-4 bullets in descrition_list
   - Enhance 2-3 bullets per experience with keywords naturally integrated
   - Update skills arrays with 2-4 new keywords MIXED throughout (not at end)
   - Example bullet enhancement: "Collected ~2000 robot trajectories using cloud storage (AWS S3) and designed dataset for model finetuning with MLOps pipeline"

5. PROJECTS SECTION - SELECTIVE INCLUSION:
   - Keep only 3-4 most relevant projects based on scoring (REMOVE others completely)
   - Enhance 2 projects: improve descriptions with 2-3 keywords
   - Update skills arrays: add 2-4 keywords MIXED in (not appended at end)
   - Keep other projects minimal/unchanged

6. SUMMARY - HONEST CAPABILITIES AND POTENTIAL:
   - Maximum 2 sentences (not 3-4!)
   - Include 3-4 most critical keywords from job posting
   - Should be punchy and direct
   - ⚠️ CRITICAL HONESTY RULE: Focus on skills, capabilities, and what the candidate CAN do, NOT false claims of experience
   - Use language like: "specializing in", "skilled in", "passionate about", "focused on", "capabilities in"
   - AVOID: "experienced in X" unless they actually have that experience documented in their CV
   - AVOID: Claiming specific domain experience they don't have (e.g., don't say "experienced in healthcare AI" if they've never worked in healthcare)
   - Good example: "AI Engineer specializing in machine learning and computer vision with strong capabilities in cloud deployment and MLOps pipelines."
   - Bad example: "AI Engineer with 5 years experience in production ML systems and enterprise cloud architecture" (if they don't have this)
   - Show how their ACTUAL skills align with the job requirements, not invented experience

7. KEYWORD PLACEMENT STRATEGY:
   - Each keyword appears 2-3 times across ENTIRE CV:
     * Once in main skills array (mixed in naturally)
     * Once in experience/project bullet or description
     * Maybe once in experience/project skills array
   - Use variations: "AWS" → "cloud infrastructure (AWS)" → "AWS Lambda" → "AWS services"
   - Include related terms: If job mentions "cloud", add both "AWS" and "Cloud Computing"
   - Never cluster all new keywords together

8. SELECTION CONSISTENCY RULES:
   - ALWAYS keep the most recent technical experience (even if relevance score is moderate)
   - ALWAYS prefer experiences/projects that demonstrate hands-on technical work over mentoring/leadership roles (unless job is leadership)
   - If two items have similar scores, keep the more recent one
   - If candidate has limited experience (only 2-3 total), keep all experiences even if one is less relevant
   - Be consistent: If you keep a certain type of project for one candidate, keep similar projects for other candidates with similar job postings

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

STEP-BY-STEP PROCESS (Follow this order):
Step 1: Score each experience (0-10) based on technical alignment, domain alignment, recency, seniority
Step 2: Score each project (0-10) based on technology overlap, problem domain, complexity
Step 3: Select top 2-3 experiences and top 3-4 projects to keep
Step 4: For kept items, identify which bullets to keep (3-4 per experience)
Step 5: Identify 8-12 keywords from job posting to add
Step 6: Enhance kept experiences/projects with keywords
Step 7: Update skills array (30-40 items, mixed placement)
Step 8: Write honest, capability-focused summary

OPTIMIZATION CHECKLIST:
1. ✓ Systematically score all experiences and projects
2. ✓ Remove content to fit one page (keep top 2-3 experiences, top 3-4 projects based on scores)
3. ✓ Keep ALL education entries unchanged
4. ✓ Summary is exactly 2 sentences focusing on capabilities, NOT false experience claims
5. ✓ Add 8-12 keywords to main skills array MIXED throughout
6. ✓ Main skills array has 30-40 items total (rich and comprehensive)
7. ✓ Enhance 4-6 bullets across kept experiences
8. ✓ Enhance 2 project descriptions
9. ✓ All new keywords are MIXED into lists, not appended at end
10. ✓ Each keyword appears 2-3 times total across CV

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
  "summary": "EXACTLY 2 sentences. Include 3-4 keywords naturally. Focus on CAPABILITIES and SKILLS, not false experience. Use: 'specializing in', 'skilled in', 'passionate about', 'capabilities in'. AVOID: 'experienced in X' unless proven in CV.",
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
    "KEEP ONLY TOP 2-3 BASED ON RELEVANCE SCORING - Must be most recent and technically aligned",
    {{
      "title": "string",
      "company": "string",
      "location": "string",
      "years": "string",
      "description": "string",
      "descrition_list": [
        "MAX 3-4 bullets per experience",
        "Enhance 2-3 bullets with keywords naturally",
        "Keep most impactful bullets based on relevance"
      ],
      "skills": ["Mix", "new", "keywords", "AWS", "throughout", "not", "at", "end"],
      "reference": "string (if exists)",
      "reference_letter_url": "string (if exists)"
    }}
  ],
  "projects": [
    "KEEP ONLY TOP 3-4 BASED ON RELEVANCE SCORING - Must have technology overlap with job",
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
    "TARGET: 30-40 items total - make it rich and comprehensive",
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
- Use systematic scoring (0-10) for consistent selection decisions
- ONE PAGE is non-negotiable - be ruthless about removing low-scoring experiences/projects
- NEVER remove education entries
- Always prefer recent (2023+) technical work over older/non-technical work
- Mix keywords naturally throughout all arrays
- Summary must be exactly 2 sentences focusing on CAPABILITIES not false claims
- Skills array should be rich (30-40 items)
- Prioritize quality, honesty, and consistency

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


def extract_cv_from_pdf_smart(pdf_path: str, model_name: str) -> dict:
    """
    Smart CV extraction from PDF: tries fast methods first, falls back to OCR if needed.
    
    Args:
        pdf_path: Path to the PDF file
        model_name: Replicate model name to use for extraction
    
    Returns:
        dict: Structured CV data matching the required JSON format
    """
    
    def read_pdf_smart(file_path: str) -> str:
        """
        Try multiple extraction methods in order of speed/reliability.
        """
        text = ""
        
        # Method 1: Try pdfplumber (fast, works for 80% of CVs)
        try:

            print("Attempting extraction with pdfplumber...")
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if text.strip():
                print("✓ Successfully extracted text directly from PDF")
                return text
            else:
                print("✗ pdfplumber found no text")
        except ImportError:
            print("✗ pdfplumber not installed, trying next method...")
        except Exception as e:
            print(f"✗ pdfplumber failed: {e}")
        
        # Method 2: Try PyMuPDF (fitz)
        try:

            print("Attempting extraction with PyMuPDF...")
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            
            if text.strip():
                print("✓ Successfully extracted text using PyMuPDF")
                return text
            else:
                print("✗ PyMuPDF found no text")
        except ImportError:
            print("✗ PyMuPDF not installed, trying next method...")
        except Exception as e:
            print(f"✗ PyMuPDF failed: {e}")
        
        # Method 3: Try PyPDF2 (basic fallback)
        try:

            print("Attempting extraction with PyPDF2...")
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            if text.strip():
                print("✓ Successfully extracted text using PyPDF2")
                return text
            else:
                print("✗ PyPDF2 found no text")
        except ImportError:
            print("✗ PyPDF2 not installed, trying OCR...")
        except Exception as e:
            print(f"✗ PyPDF2 failed: {e}")
        
        # Method 4: Fallback to OCR (slow but works on scanned PDFs)
        print("⚠ No text extraction worked, attempting OCR (this may take a minute)...")
        try:

            
            images = convert_from_path(file_path, dpi=300)
            for i, image in enumerate(images):
                print(f"  OCR processing page {i+1}/{len(images)}...")
                page_text = pytesseract.image_to_string(image, lang='eng')
                text += page_text + "\n"
            
            if text.strip():
                print("✓ Successfully extracted text using OCR")
                return text
            else:
                print("✗ OCR found no text")
        except ImportError:
            print("✗ OCR libraries not installed. Install pytesseract and pdf2image for scanned PDF support.")
        except Exception as e:
            print(f"✗ OCR failed: {e}")
            print("Note: OCR requires Tesseract to be installed on your system.")
        
        raise ValueError(
            "Could not extract any text from PDF using any method. "
            "The PDF might be empty, corrupted, or require OCR (install pytesseract and Tesseract)."
        )
    
    # Extract text from PDF
    cv_text = read_pdf_smart(pdf_path)
    
    if not cv_text.strip():
        raise ValueError("Extracted text is empty.")
    
    print(f"\nExtracted {len(cv_text)} characters from PDF")
    print("Sending to LLM for structured extraction...\n")
    
    # Create extraction prompt
    prompt = f"""
You are an expert CV parser. Extract ALL information from the provided CV text and structure it into a specific JSON format.

CRITICAL INSTRUCTIONS:
1. Extract ALL information accurately - do not skip or summarize
2. Maintain exact dates, names, and details as written
3. If information is missing, use empty strings "" or empty arrays []
4. Do NOT invent or assume information that isn't in the CV
5. Return ONLY valid JSON, no markdown, no commentary

CV TEXT TO PARSE:
{cv_text}

REQUIRED JSON STRUCTURE (match this exactly):
{{
  "personal_info": {{
    "name": "Full name from CV",
    "email": "email address",
    "phone": "phone number",
    "nationality": "nationality if mentioned, otherwise empty string",
    "age": age_as_number_if_mentioned_otherwise_0,
    "linkedin": "LinkedIn URL if present",
    "github": "GitHub URL if present",
    "languages": ["array of languages with proficiency levels"]
  }},
  "summary": "Professional summary or objective statement - keep it as written in CV",
  "education": [
    {{
      "degree": "Full degree name",
      "institution": "University/School name",
      "location": "City, Country",
      "year": "Date range (e.g., 'Sep 2020 - Jul 2023')",
      "description": "Additional details about specialization, coursework, etc.",
      "grade": "GPA or grade if mentioned"
    }}
  ],
  "experience": [
    {{
      "title": "Job title",
      "company": "Company name",
      "location": "City, Country",
      "years": "Date range (e.g., 'Jan 2025 - Jul 2025')",
      "description": "Brief one-line description of role or thesis if mentioned",
      "descrition_list": [
        "First responsibility/achievement bullet point",
        "Second responsibility/achievement bullet point",
        "Continue for all bullet points listed"
      ],
      "skills": ["array", "of", "technologies", "and", "skills", "used"],
      "reference": "Reference person name if mentioned, otherwise empty string",
      "reference_letter_url": "URL if provided, otherwise empty string"
    }}
  ],
  "projects": [
    {{
      "name": "Project name",
      "role": "Your role in the project",
      "year": "Year (e.g., '2024')",
      "description": "Project description as written",
      "skills": ["technologies", "used", "in", "project"],
      "url": "Project URL/GitHub link if provided"
    }}
  ],
  "skills": [
    "Extract all skills mentioned anywhere in CV",
    "Include programming languages, frameworks, tools, methodologies",
    "Keep as individual items in array"
  ]
}}

EXTRACTION RULES:
- For experience descrition_list: Extract each bullet point as a separate array item
- For skills arrays: Extract technologies mentioned in that specific experience/project
- For main skills array: Compile ALL technical skills mentioned throughout the CV
- Dates: Keep in original format from CV
- If CV has sections not matching this structure, map them to the closest equivalent
- If age is not explicitly stated, set to 0
- Preserve all URLs exactly as they appear
- Note: "descrition_list" spelling is intentional (keep the typo)

IMPORTANT: Return ONLY the JSON object. No explanation, no markdown formatting, no ```json``` tags.

BEGIN EXTRACTION:
"""

    # Call LLM for extraction
    print("Calling LLM for extraction...")
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
    
    # Parse JSON
    try:
        cv_data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON. Error: {str(e)}\n\nReceived content:\n{content[:500]}...")
    
    # Validate required fields
    required_fields = ["personal_info", "summary", "education", "experience", "projects", "skills"]
    for field in required_fields:
        if field not in cv_data:
            raise ValueError(f"Missing required field in extracted data: {field}")
    
    print("✓ Successfully extracted and structured CV data\n")
    return cv_data


def save_cv_to_json(cv_data: dict, output_path: str) -> None:
    """
    Save CV data to a JSON file.
    
    Args:
        cv_data: Dictionary containing CV data
        output_path: Path where JSON file should be saved
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cv_data, f, indent=2, ensure_ascii=False)
        print(f"✓ CV data successfully saved to {output_path}")
    except Exception as e:
        raise ValueError(f"Error saving JSON file: {str(e)}")