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
from typing import Dict, Any, Tuple, List

load_dotenv()
api_token = os.getenv("REPLICATE_API_TOKEN")

if not api_token:
    raise ValueError("REPLICATE_API_TOKEN is not set in environment variables.")

def generate_optimized_profile_with_validation(
    profile: dict, 
    job_info: dict, 
    model_name: str,
    max_retries: int = 2
) -> dict:
    """
    Generate and validate optimized CV with automatic corrections.
    
    Args:
        profile: Original CV data
        job_info: Job posting information
        model_name: Replicate model name
        max_retries: Maximum number of correction attempts
        
    Returns:
        Validated and corrected CV data
    """
    
    for attempt in range(max_retries + 1):
        print(f"\n{'='*60}")
        print(f"GENERATION ATTEMPT {attempt + 1}/{max_retries + 1}")
        print(f"{'='*60}\n")
        
        # Generate CV
        cv_data = generate_optimized_profile(profile, job_info, model_name)
        
        # Validate
        is_valid, issues = _validate_cv_strict(cv_data, profile, job_info)
        
        if is_valid:
            print("✅ CV passed all validation checks!")
            return cv_data
        
        if attempt < max_retries:
            print(f"\n⚠️ Validation failed. Issues found: {len(issues)}")
            for issue in issues:
                print(f"   - {issue['message']}")
            
            # Use LLM to fix issues
            print(f"\n🔧 Attempting to fix issues (attempt {attempt + 1}/{max_retries})...")
            cv_data = _fix_cv_with_llm(cv_data, profile, issues, job_info, model_name)
        else:
            print(f"\n⚠️ Maximum retries reached. Applying emergency fixes...")
            cv_data = _apply_emergency_fixes(cv_data, profile, issues)
    
    return cv_data


def _validate_cv_strict(cv_data: Dict, original_profile: Dict, job_info: Dict) -> Tuple[bool, List[Dict]]:
    """Strict validation with detailed issue reporting."""
    
    issues = []
    
    # 1. Check for invented experiences
    original_exp_keys = {
        (exp.get('title', ''), exp.get('company', '')) 
        for exp in original_profile.get('experience', [])
    }
    output_exp_keys = {
        (exp.get('title', ''), exp.get('company', '')) 
        for exp in cv_data.get('experience', [])
    }
    
    invented_exp = output_exp_keys - original_exp_keys
    if invented_exp:
        issues.append({
            "type": "invented_experience",
            "severity": "critical",
            "message": f"Created non-existent experiences: {invented_exp}",
            "invented": list(invented_exp)
        })
    
    # 2. Check for invented projects
    original_proj_keys = {proj.get('name', '') for proj in original_profile.get('projects', [])}
    output_proj_keys = {proj.get('name', '') for proj in cv_data.get('projects', [])}
    
    invented_proj = output_proj_keys - original_proj_keys
    if invented_proj:
        issues.append({
            "type": "invented_project",
            "severity": "critical",
            "message": f"Created non-existent projects: {invented_proj}",
            "invented": list(invented_proj)
        })
    
    # 3. Check content limits (one-page constraint)
    exp_count = len(cv_data.get('experience', []))
    proj_count = len(cv_data.get('projects', []))
    
    if exp_count > 3:
        issues.append({
            "type": "too_many_experiences",
            "severity": "high",
            "message": f"Too many experiences: {exp_count} (max 3)",
            "count": exp_count
        })
    
    if proj_count > 4:
        issues.append({
            "type": "too_many_projects",
            "severity": "high",
            "message": f"Too many projects: {proj_count} (max 4)",
            "count": proj_count
        })
    
    total_items = exp_count + proj_count
    if total_items > 7:
        issues.append({
            "type": "too_much_content",
            "severity": "high",
            "message": f"Total items {total_items} (exp+proj). Max 7 for one page.",
            "total": total_items
        })
    
    # 4. Check for excessive bullets
    for i, exp in enumerate(cv_data.get('experience', [])):
        bullets = len(exp.get('descrition_list', []))
        if bullets > 4:
            issues.append({
                "type": "too_many_bullets",
                "severity": "medium",
                "message": f"Experience {i} has {bullets} bullets (max 4)",
                "experience_index": i,
                "count": bullets
            })
    
    # 5. Check required fields
    if not cv_data.get('personal_info', {}).get('name'):
        issues.append({
            "type": "missing_name",
            "severity": "critical",
            "message": "Missing personal name"
        })
    
    if not cv_data.get('summary', '').strip():
        issues.append({
            "type": "missing_summary",
            "severity": "high",
            "message": "Summary is empty"
        })
    
    if len(cv_data.get('skills', [])) < 10:
        issues.append({
            "type": "too_few_skills",
            "severity": "medium",
            "message": f"Only {len(cv_data.get('skills', []))} skills (min 15-20 recommended)"
        })
    
    # 6. Check for empty experiences/projects
    if exp_count == 0:
        issues.append({
            "type": "no_experiences",
            "severity": "critical",
            "message": "No experiences in output"
        })
    
    if proj_count == 0:
        issues.append({
            "type": "no_projects",
            "severity": "high",
            "message": "No projects in output"
        })
    
    is_valid = len([i for i in issues if i['severity'] == 'critical']) == 0
    
    return is_valid, issues


def _fix_cv_with_llm(cv_data: Dict, original_profile: Dict, issues: List[Dict], 
                     job_info: Dict, model_name: str) -> Dict:
    """Use LLM to fix validation issues."""
    
    issues_summary = "\n".join([f"- {issue['message']}" for issue in issues])
    
    prompt = f"""
You are fixing a CV that failed validation. Apply ONLY the necessary corrections.

VALIDATION ISSUES FOUND:
{issues_summary}

ORIGINAL PROFILE (for reference - you can ONLY select from here):
{json.dumps(original_profile, indent=2, ensure_ascii=False)}

CURRENT CV OUTPUT (with issues):
{json.dumps(cv_data, indent=2, ensure_ascii=False)}

CORRECTION INSTRUCTIONS:
1. If experiences/projects were invented: REMOVE them, select only from original profile
2. If too many items: REMOVE lowest-relevance ones until limits met (max 3 exp, 4 proj)
3. If too many bullets: KEEP only 3-4 best bullets per experience
4. If missing data: ADD from original profile
5. Keep ALL other content exactly as-is

CRITICAL: 
- ONLY select experiences from original "experience" array
- ONLY select projects from original "projects" array
- Do not create new content
- Just remove excess and select from originals

OUTPUT corrected JSON (no markdown):
"""

    output = replicate.run(model_name, input={"prompt": prompt})
    content = "".join([str(x) for x in output]).strip()
    
    # Clean markdown
    if content.startswith("```json"):
        content = content.split("```json")[1]
    if content.startswith("```"):
        content = content.split("```")[1]
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]
    content = content.strip()
    
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("⚠️ LLM fix failed, applying emergency fixes")
        return _apply_emergency_fixes(cv_data, original_profile, issues)


def _apply_emergency_fixes(cv_data: Dict, original_profile: Dict, issues: List[Dict]) -> Dict:
    """Apply hard-coded fixes when LLM fails."""
    
    corrected = cv_data.copy()
    
    print("🚨 Applying emergency fixes...")
    
    # Fix 1: Remove invented experiences
    original_exp_keys = {
        (exp.get('title', ''), exp.get('company', '')) 
        for exp in original_profile.get('experience', [])
    }
    
    valid_experiences = []
    for exp in corrected.get('experience', []):
        key = (exp.get('title', ''), exp.get('company', ''))
        if key in original_exp_keys:
            valid_experiences.append(exp)
        else:
            print(f"   Removed invented experience: {key}")
    
    corrected['experience'] = valid_experiences[:3]  # Max 3
    
    # Fix 2: Remove invented projects
    original_proj_keys = {proj.get('name', '') for proj in original_profile.get('projects', [])}
    
    valid_projects = []
    for proj in corrected.get('projects', []):
        name = proj.get('name', '')
        if name in original_proj_keys:
            valid_projects.append(proj)
        else:
            print(f"   Removed invented project: {name}")
    
    corrected['projects'] = valid_projects[:4]  # Max 4
    
    # Fix 3: Trim bullets
    for i, exp in enumerate(corrected.get('experience', [])):
        bullets = exp.get('descrition_list', [])
        if len(bullets) > 4:
            corrected['experience'][i]['descrition_list'] = bullets[:4]
            print(f"   Trimmed bullets for experience {i}")
    
    # Fix 4: Ensure minimum content if we removed too much
    if len(corrected.get('experience', [])) < 2 and len(original_profile.get('experience', [])) >= 2:
        print("   Restoring minimum experiences from original")
        corrected['experience'] = original_profile['experience'][:2]
    
    if len(corrected.get('projects', [])) < 3 and len(original_profile.get('projects', [])) >= 3:
        print("   Restoring minimum projects from original")
        corrected['projects'] = original_profile['projects'][:3]
    
    # Fix 5: Ensure education is preserved
    if not corrected.get('education'):
        corrected['education'] = original_profile.get('education', [])
    
    # Fix 6: Trim skills if too many
    if len(corrected.get('skills', [])) > 30:
        corrected['skills'] = corrected['skills'][:25]
        print(f"   Trimmed skills to 25")
    
    return corrected

def generate_optimized_profile(profile: dict, job_info: dict, model_name: str) -> dict:
    """
    Generate an ATS-optimized CV that strategically incorporates job posting keywords
    while maintaining authenticity and fitting on ONE page.
    """
    prompt = f"""
  You are an expert ATS (Applicant Tracking System) optimization specialist. Your goal is to create a ONE-PAGE CV that maximizes ATS score while looking authentic.

  🚨 CRITICAL RULE: YOU MUST ONLY SELECT FROM EXISTING DATA 🚨
  - You can ONLY choose experiences that exist in the "experience" array
  - You can ONLY choose projects that exist in the "projects" array
  - DO NOT create new entries
  - DO NOT merge experiences into projects or vice versa
  - DO NOT invent job titles, companies, or roles
  - SELECTION ONLY - not creation

  CRITICAL PAGE LIMIT RULE:
  ⚠️ The CV MUST fit on ONE page when rendered. You MUST remove content to achieve this:
  - Keep maximum 2-3 experiences from the "experience" array (remove least relevant)
  - Keep maximum 3-4 projects from the "projects" array (remove least relevant)
  - Each experience should have 3-4 bullets max in descrition_list
  - Prioritize recent and relevant entries over older/unrelated ones

  EDUCATION CONDENSING RULE:
  🎓 MANDATORY EDUCATION CONDENSING LOGIC:
  
  1. DOUBLE/JOINT DEGREE DETECTION:
     - Look for education entries with SAME or OVERLAPPING years (e.g., "sep 2023 - current" and "sep 2023 - sep 2024")
     - Look for entries mentioning "Double Master", "Joint Degree", "EIT Digital", or similar programs
     - Look for entries from different institutions but same time period (exchange programs)
  
  2. CONDENSING RULES:
     - IF multiple entries are clearly part of the same program → CONDENSE to 1 entry
     - IF Bachelor's + Master's (different time periods) → Keep separate
     - IF same degree level with overlapping years → CONDENSE to 1 entry
  
  3. HOW TO CONDENSE:
     - Combine degree names: "Double MSc in Robotics and Artificial Intelligence"
     - Combine institutions: "University of Trento & Aalto University" 
     - Combine locations: "Trento, Italy & Espoo, Finland"
     - Use the LONGEST time span: "Sep 2023 - Aug 2025"
     - Combine descriptions: Include ALL specializations from both entries
     - Keep best grade if multiple exist
  
  EXAMPLE CONDENSING:
  FROM 4 entries → TO 2 entries:
  Entry 1: "Double MSc in Robotics and Artificial Intelligence - University of Trento & Aalto University (Sep 2023 - Aug 2025)"
  Entry 2: "BSc in Computer, Communications and Electronic Engineering - University of Trento (Sep 2020 - Jul 2023)"

  OPTIMIZATION STRATEGY:

  1. CONTENT SELECTION - SYSTEMATIC RELEVANCE SCORING (DO THIS FIRST):
     
     A. EXPERIENCE RELEVANCE SCORING:
     Look at the "experience" array in the input. For EACH entry, assign a score (0-10):
     - Technical alignment: Does it use similar technologies/skills as the job? (0-4 points)
     - Domain alignment: Is it in a similar field/industry? (0-3 points)
     - Recency: How recent is it? (0-2 points: 2024-2025=2pts, 2022-2023=1pt, before 2022=0pts)
     - Seniority/Impact: Does the role level match the job posting? (0-1 point)
     
     THEN: Select the top 2-3 entries with highest scores. Copy those entries to output, remove the rest.
     
     B. PROJECT RELEVANCE SCORING:
     Look at the "projects" array in the input. For EACH entry, assign a score (0-10):
     - Technology overlap: Does it use tools/frameworks mentioned in job posting? (0-5 points)
     - Problem domain: Does it solve similar problems as the job? (0-3 points)
     - Complexity/Impact: Is it a substantial, impressive project? (0-2 points)
     
     THEN: Select the top 3-4 entries with highest scores. Copy those entries to output, remove the rest.
     
     C. VERIFICATION:
     - Count experiences in input: {len(profile.get('experience', []))} experiences exist
     - Count projects in input: {len(profile.get('projects', []))} projects exist
     - You can only select from these existing entries
     - Output should have 2-3 experiences + 3-4 projects = 5-7 total items

  2. KEYWORD IDENTIFICATION:
     - Extract 10-15 critical technical keywords from the job posting
     - Focus on: specific tools (AWS, Docker, Kubernetes), methodologies (MLOps, Agile, CI/CD), technical skills

  3. SKILLS SECTION - RICH AND COMPREHENSIVE:
     - Goal: Create a rich skills array (20-25 items total)
     - Add 8-12 critical keywords from job posting
     - Keep most original skills, only remove 2-3 truly irrelevant ones
     - ⚠️ CRITICAL: Mix new keywords THROUGHOUT the array, not just at the end
     - Pattern: [original, original, NEW_KEYWORD, original, original, NEW_KEYWORD, original]

  4. EXPERIENCE SECTION - ENHANCE EXISTING ONLY:
     - Take the 2-3 selected experiences from input
     - For each: keep title, company, location, years, description EXACTLY as-is
     - Only modify: descrition_list (enhance 2-3 bullets with keywords) and skills array
     - Limit descrition_list to 3-4 best bullets
     - Add 2-4 new keywords to skills array, mixed throughout

  5. PROJECTS SECTION - ENHANCE EXISTING ONLY:
     - Take the 3-4 selected projects from input
     - For each: keep name, role, year, url EXACTLY as-is
     - Only modify: description (add 1-2 keywords naturally) and skills array
     - Add 2-4 new keywords to skills array, mixed throughout

  6. SUMMARY - HONEST CAPABILITIES:
     - Maximum 2 sentences
     - Include 3-4 most critical keywords from job posting
     - Focus on skills and capabilities: "specializing in", "skilled in", "passionate about"
     - AVOID: "experienced in X" unless they actually have documented experience

  7. KEYWORD PLACEMENT STRATEGY:
     - Each keyword appears 2-3 times across ENTIRE CV
     - Use variations: "AWS" → "cloud infrastructure" → "AWS services"
     - Never cluster all new keywords together

  8. EDUCATION - MANDATORY CONDENSING:
     - ALWAYS check for overlapping years or double degree programs
     - Bachelor's and Master's with different years = keep separate
     - Multiple entries with same/overlapping years = CONDENSE into 1 entry
     - Example: 4 education entries about the same double degree → condense to 1 entry
     - Make descriptions concise (max 1 sentence)
     - Format dates consistently (e.g., "Sep 2023 - Aug 2025")


  INPUT DATA:

  Candidate Profile:
  {json.dumps(profile, indent=2, ensure_ascii=False)}

  Job Posting:
  {json.dumps(job_info, indent=2, ensure_ascii=False)}

  MANDATORY PROCESS:
  Step 1: List all experiences from input and score each (0-10)
  Step 2: List all projects from input and score each (0-10)
  Step 3: Select top 2-3 experiences BY INDEX from input array
  Step 4: Select top 3-4 projects BY INDEX from input array
  Step 5: ANALYZE EDUCATION: Check for overlapping years/double degrees and plan condensing
  Step 6: Copy selected entries, enhance with keywords
  Step 7: Build final JSON with ONLY selected entries
  Step 8: CONDENSE EDUCATION: Merge overlapping/double degree entries into fewer entries

  VERIFICATION CHECKLIST BEFORE OUTPUT:
  □ Did I create any new experience entries? (If YES, this is WRONG - remove them)
  □ Did I create any new project entries? (If YES, this is WRONG - remove them)
  □ Did I mix up experiences and projects? (If YES, this is WRONG - fix it)
  □ Are all experiences from the original "experience" array? (Must be YES)
  □ Are all projects from the original "projects" array? (Must be YES)
  □ Did I keep company names, job titles exactly as input? (Must be YES)
  □ Did I keep project names, years, URLs exactly as input? (Must be YES)
  □ CRITICAL: Did I condense education entries with overlapping years/double degrees? (Must be YES if applicable)
  □ Do I have fewer education entries in output than input due to condensing? (Should be YES if there were overlapping degrees)

  OUTPUT REQUIREMENTS:
  Return ONLY valid JSON, no markdown, no commentary.

  {{
    "personal_info": {{
    "name": "string - EXACT from input",
    "email": "string - EXACT from input",
    "phone": "string - EXACT from input",
    "nationality": "string - EXACT from input",
    "age": number - EXACT from input,
    "linkedin": "string - EXACT from input",
    "github": "string - EXACT from input",
    "languages": ["array - EXACT from input"]
    }},
    "summary": "EXACTLY 2 sentences with 3-4 keywords. Focus on capabilities, not false claims.",
    "education": [
    "MANDATORY: CONDENSE overlapping/double degrees into FEWER entries than input",
    "Example: 4 input entries about same double degree → 1 output entry",
    "Keep Bachelor's separate from Master's if different time periods",
    {{
      "degree": "EXACT from input, or COMBINED if condensing (e.g., 'Double MSc in Robotics and AI')",
      "institution": "EXACT from input, or COMBINED if condensing (e.g., 'Univ of Trento & Aalto Univ')",
      "location": "EXACT from input, or COMBINED if condensing (e.g., 'Trento, IT & Espoo, FI')",
      "year": "IMPORTANT: Format as 'Mon YYYY - Mon YYYY' using LONGEST span if condensing",
      "description": "Keep existing but max 1 sentence, COMBINE if condensing",
      "grade": "EXACT from input, keep best grade if condensing"
    }}
    ],
    "experience": [
    "SELECT 2-3 ENTRIES FROM INPUT 'experience' ARRAY ONLY",
    "DO NOT CREATE NEW ENTRIES",
    {{
      "title": "EXACT from input",
      "company": "EXACT from input",
      "location": "EXACT from input",
      "years": "EXACT from input",
      "description": "EXACT from input",
      "descrition_list": [
      "Keep 3-4 best bullets from input",
      "Enhance 2-3 with keywords naturally"
      ],
      "skills": ["Maximum 10 skills", "Mix new keywords throughout"],
      "reference": "EXACT from input or empty",
      "reference_letter_url": "EXACT from input or empty"
    }}
    ],
    "projects": [
    "SELECT 3-4 ENTRIES FROM INPUT 'projects' ARRAY ONLY",
    "DO NOT CREATE NEW ENTRIES",
    {{
      "name": "EXACT from input",
      "role": "EXACT from input",
      "year": "EXACT from input",
      "description": "Enhance with 1-2 keywords",
      "skills": ["Maximum 10 skills", "Mix new keywords throughout"],
      "url": "EXACT from input"
    }}
    ],
    "skills": [
    "TARGET: 20-25 items total",
    "Mix new keywords throughout - NOT at end",
    "Pattern: original, original, NEW, original, NEW, original"
    ]
  }}

  FINAL WARNING: 
  - If you create ANY entry not in the input arrays, the output is INVALID
  - If you mix experiences and projects, the output is INVALID
  - SELECTION and ENHANCEMENT only - NO CREATION

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

    # Post-processing validation
    input_experience_titles = {exp.get('title', '') + exp.get('company', '') for exp in profile.get('experience', [])}
    output_experience_titles = {exp.get('title', '') + exp.get('company', '') for exp in optimized_cv.get('experience', [])}
    
    input_project_names = {proj.get('name', '') for proj in profile.get('projects', [])}
    output_project_names = {proj.get('name', '') for proj in optimized_cv.get('projects', [])}
    
    # Check for invented experiences
    if not output_experience_titles.issubset(input_experience_titles):
        print("⚠️ WARNING: LLM created experiences not in input!")
        invented = output_experience_titles - input_experience_titles
        print(f"Invented experiences: {invented}")
    
    # Check for invented projects
    if not output_project_names.issubset(input_project_names):
        print("⚠️ WARNING: LLM created projects not in input!")
        invented = output_project_names - input_project_names
        print(f"Invented projects: {invented}")

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
    Intelligently fills in missing structured information while preserving existing content.
    
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
            import fitz
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
            import PyPDF2
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
            from pdf2image import convert_from_path
            import pytesseract
            
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
    print("Sending to LLM for structured extraction and intelligent formatting...\n")
    
    # Create extraction prompt with intelligent filling
    prompt = f"""
      You are an expert CV parser with intelligent formatting capabilities. Your task is to extract information from the CV and structure it properly, filling in missing structured elements where appropriate.

      CRITICAL INSTRUCTIONS:

      1. WHAT TO PRESERVE EXACTLY AS-IS (DO NOT MODIFY):
      - Personal information (name, email, phone, LinkedIn, GitHub, etc.)
      - Education details (degree names, institutions, grades)
      - Company names, job titles, locations
      - Project names, years, and URLs
      - Any reference names and URLs

      2. WHAT TO INTELLIGENTLY FORMAT/FILL:
      
      A. EXPERIENCE DESCRIPTIONS → descrition_list:
        - If experience has a paragraph description, convert it into bullet points (descrition_list array)
        - Break down responsibilities and achievements into 3-5 clear bullet points
        - Each bullet should start with an action verb and be concise
        - If already in bullet format, preserve them
        - If very minimal description, create 2-3 bullets based on what's written
        
      B. PROJECT DESCRIPTIONS:
        - If project description is missing or very brief, enhance it slightly based on the project name and skills
        - Keep it to 1-2 sentences maximum
        - If good description exists, keep it
        
      C. SKILLS ARRAYS:
        - For experience "skills" array: Extract/infer technologies mentioned in the job description
        - For project "skills" array: Extract/infer technologies mentioned in the project description
        - For main "skills" array: Compile ALL skills mentioned throughout the CV
        - If skills section is missing, create it by extracting technologies from all experiences and projects
        
      D. SUMMARY:
        - If summary exists, keep it exactly as written
        - If summary is missing or very generic, create a brief 1-2 sentence summary based on their experiences and skills
        - Focus on their primary expertise and background

      3. TIME INTERVAL FORMATTING (IMPORTANT):
      - For every date or time interval (in education, experience, projects, etc.), rephrase it as "Mon YYYY - Mon YYYY" (e.g., "Sep 2018 - Jun 2022")
      - Remove any words or phrases indicating duration (such as "7 years", "for 2 years", "duration: 3 years", etc.)
      - If only a single date is present, format as "Mon YYYY"
      - Use English month abbreviations (Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec)
      - If dates are missing, leave the field as an empty string

      4. EXTRACTION LOGIC:

      Example transformation for experience:
      
      ORIGINAL: "Software Engineer at Google. Worked on backend systems. (2015-2022, 7 years)"
      
      TRANSFORM TO:
      {{
        "title": "Software Engineer",
        "company": "Google",
        "years": "Jan 2015 - Dec 2022",
        "descrition_list": [
        "Developed and maintained backend systems",
        "Collaborated with cross-functional teams on system architecture"
        ],
        "skills": ["Backend Development", "System Architecture"]
      }}

      5. DO NOT INVENT:
      - Do not invent companies, projects, or experiences that don't exist
      - Do not add skills the person clearly doesn't have
      - Do not change names or factual information
      - Only infer/extract what's reasonable from the existing text

      CV TEXT TO PARSE:
      {cv_text}

      REQUIRED JSON STRUCTURE:
      {{
      "personal_info": {{
        "name": "Full name from CV - EXACT",
        "email": "email address - EXACT",
        "phone": "phone number - EXACT",
        "nationality": "nationality if mentioned, otherwise empty string",
        "age": age_as_number_if_mentioned_otherwise_0,
        "linkedin": "LinkedIn URL if present - EXACT",
        "github": "GitHub URL if present - EXACT",
        "languages": ["array of languages with proficiency levels - EXACT or inferred from CV"]
      }},
      "summary": "Keep existing summary OR create brief 1-2 sentence summary if missing",
      "education": [
        {{
        "degree": "Full degree name - EXACT",
        "institution": "University/School name - EXACT",
        "location": "City, Country - EXACT",
        "year": "Date range - formatted as 'Mon YYYY - Mon YYYY', or 'Mon YYYY' if only one date, or empty if missing",
        "description": "Specialization details - EXACT or empty if not mentioned",
        "grade": "GPA/grade - EXACT or empty if not mentioned"
        }}
      ],
      "experience": [
        {{
        "title": "Job title - EXACT",
        "company": "Company name - EXACT",
        "location": "City, Country - EXACT",
        "years": "Date range - formatted as 'Mon YYYY - Mon YYYY', or 'Mon YYYY' if only one date, or empty if missing",
        "description": "Brief one-line description - EXACT or inferred",
        "descrition_list": [
          "Convert paragraph descriptions into 3-5 bullet points",
          "Each bullet: action verb + achievement/responsibility",
          "Extract from existing text, do not invent"
        ],
        "skills": ["Extract technologies/tools mentioned in this role"],
        "reference": "Reference name if mentioned - EXACT or empty",
        "reference_letter_url": "URL if provided - EXACT or empty"
        }}
      ],
      "projects": [
        {{
        "name": "Project name - EXACT",
        "role": "Your role - EXACT or inferred from context",
        "year": "Date range - formatted as 'Mon YYYY - Mon YYYY', or 'Mon YYYY' if only one date, or empty if missing",
        "description": "Keep good description OR enhance if too brief (1-2 sentences max)",
        "skills": ["Extract technologies mentioned OR infer from project name/description"],
        "url": "URL - EXACT or empty"
        }}
      ],
      "skills": [
        "Extract ALL skills from entire CV",
        "Include: programming languages, frameworks, tools, platforms, methodologies",
        "Infer technologies mentioned in any experience or project",
        "Create this array even if CV has no skills section"
      ]
      }}

      FORMATTING RULES:
      - descrition_list: ALWAYS create this as an array of 3-5 bullet points per experience
      - Skills arrays: ALWAYS populate by extracting from descriptions
      - Keep the typo "descrition_list" (not "description_list")
      - Use empty strings "" for missing optional fields
      - Use empty arrays [] for missing array fields
      - Preserve all URLs, emails, phone numbers exactly

      IMPORTANT: Return ONLY the JSON object. No explanation, no markdown formatting, no ```json``` tags.

      BEGIN EXTRACTION AND INTELLIGENT FORMATTING:
      """

    # Call LLM for extraction
    print("Calling LLM for extraction and formatting...")
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
    
    print("✓ Successfully extracted and formatted CV data\n")
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