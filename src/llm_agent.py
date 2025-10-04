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

# Prompt loader
def load_prompt(name: str) -> str:
    """Load prompt from prompts/ directory."""
    prompt_path = os.path.join("prompts", f"{name}.txt")
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def generate_optimized_profile_with_validation(
    profile: dict, 
    job_info: dict, 
    model_name: str,
    max_retries: int = 2
) -> dict:
    """Generate and validate optimized CV with automatic corrections."""
    
    for attempt in range(max_retries + 1):
        print(f"\n{'='*60}")
        print(f"ATTEMPT {attempt + 1}/{max_retries + 1}")
        print(f"{'='*60}\n")
        
        # Generate
        cv_data = generate_optimized_profile(profile, job_info, model_name)
        
        # Validate
        is_valid, issues = _validate_cv_strict(cv_data, profile, job_info)
        
        if is_valid:
            print("✅ Validation passed!")
            return cv_data
        
        print(f"\n⚠️ {len(issues)} issues found:")
        for issue in issues:
            severity = issue['severity'].upper()
            print(f"   [{severity}] {issue['message']}")
        
        if attempt < max_retries:
            print(f"\n🔧 Fixing (attempt {attempt + 1}/{max_retries})...")
            cv_data = _fix_cv_with_llm(cv_data, profile, issues, job_info, model_name)
        else:
            print(f"\n🚨 Max retries reached. Emergency fixes...")
            cv_data = _apply_emergency_fixes(cv_data, profile, issues)
    
    # Final validation
    is_valid, remaining_issues = _validate_cv_strict(cv_data, profile, job_info)
    if remaining_issues:
        print(f"\n⚠️ {len(remaining_issues)} issues remain after all fixes")
    
    return cv_data


def _validate_cv_strict(cv_data: Dict, original_profile: Dict, job_info: Dict) -> Tuple[bool, List[Dict]]:
    """Strict validation with detailed reporting."""
    issues = []
    
    # 1. Invented experiences
    orig_exp = {(e.get('title',''), e.get('company','')) for e in original_profile.get('experience',[])}
    out_exp = {(e.get('title',''), e.get('company','')) for e in cv_data.get('experience',[])}
    invented_exp = out_exp - orig_exp
    
    if invented_exp:
        for exp in invented_exp:
            issues.append({
                "type": "invented_experience",
                "severity": "critical",
                "message": f"Invented experience: {exp[0]} at {exp[1]}"
            })
    
    # 2. Invented projects
    orig_proj = {p.get('name','') for p in original_profile.get('projects',[])}
    out_proj = {p.get('name','') for p in cv_data.get('projects',[])}
    invented_proj = out_proj - orig_proj
    
    if invented_proj:
        for proj in invented_proj:
            issues.append({
                "type": "invented_project",
                "severity": "critical",
                "message": f"Invented project: {proj}"
            })
    
    # 3. Content limits
    exp_count = len(cv_data.get('experience',[]))
    proj_count = len(cv_data.get('projects',[]))
    
    if exp_count > 3:
        issues.append({
            "type": "too_many_experiences",
            "severity": "high",
            "message": f"{exp_count} experiences (max 3)"
        })
    
    if proj_count > 4:
        issues.append({
            "type": "too_many_projects",
            "severity": "high",
            "message": f"{proj_count} projects (max 4)"
        })
    
    if exp_count + proj_count > 7:
        issues.append({
            "type": "too_much_content",
            "severity": "high",
            "message": f"{exp_count + proj_count} total items (max 7)"
        })
    
    # 4. Bullet limits
    for i, exp in enumerate(cv_data.get('experience',[])):
        bullets = len(exp.get('descrition_list',[]))
        if bullets > 4:
            issues.append({
                "type": "too_many_bullets",
                "severity": "medium",
                "message": f"Experience {i}: {bullets} bullets (max 4)",
                "exp_index": i
            })
    
    # 5. Required fields
    if not cv_data.get('personal_info',{}).get('name'):
        issues.append({"type": "missing_name", "severity": "critical", "message": "Missing name"})
    
    if not cv_data.get('summary','').strip():
        issues.append({"type": "missing_summary", "severity": "high", "message": "Empty summary"})
    
    if exp_count == 0:
        issues.append({"type": "no_experiences", "severity": "critical", "message": "No experiences"})
    
    if proj_count == 0:
        issues.append({"type": "no_projects", "severity": "high", "message": "No projects"})
    
    is_valid = not any(i['severity'] == 'critical' for i in issues)
    return is_valid, issues


def _fix_cv_with_llm(cv_data: Dict, original_profile: Dict, issues: List[Dict], 
                     job_info: Dict, model_name: str) -> Dict:
    """LLM-based fix."""
    prompt_template = load_prompt("cv_fix")
    issues_text = "\n".join([f"- {i['message']}" for i in issues])
    
    prompt = prompt_template.format(
        issues=issues_text,
        original_profile=json.dumps(original_profile, indent=2),
        cv_data=json.dumps(cv_data, indent=2)
    )
    
    try:
        output = replicate.run(model_name, input={"prompt": prompt})
        content = "".join([str(x) for x in output]).strip()
        content = _clean_json(content)
        return json.loads(content)
    except Exception as e:
        print(f"⚠️ LLM fix failed: {e}")
        return _apply_emergency_fixes(cv_data, original_profile, issues)


def _apply_emergency_fixes(cv_data: Dict, original_profile: Dict, issues: List[Dict]) -> Dict:
    """Hard-coded Python fixes."""
    corrected = json.loads(json.dumps(cv_data))  # Deep copy
    
    print("🚨 Emergency fixes:")
    
    # Fix invented experiences
    orig_exp = {(e.get('title',''), e.get('company','')) for e in original_profile.get('experience',[])}
    valid_exp = [e for e in corrected.get('experience',[]) 
                 if (e.get('title',''), e.get('company','')) in orig_exp]
    if len(valid_exp) < len(corrected.get('experience',[])):
        print(f"   Removed {len(corrected.get('experience',[])) - len(valid_exp)} invented experiences")
    corrected['experience'] = valid_exp[:3]
    
    # Fix invented projects
    orig_proj = {p.get('name','') for p in original_profile.get('projects',[])}
    valid_proj = [p for p in corrected.get('projects',[]) if p.get('name','') in orig_proj]
    if len(valid_proj) < len(corrected.get('projects',[])):
        print(f"   Removed {len(corrected.get('projects',[])) - len(valid_proj)} invented projects")
    corrected['projects'] = valid_proj[:4]
    
    # Trim bullets
    for i, exp in enumerate(corrected.get('experience',[])):
        bullets = exp.get('descrition_list',[])
        if len(bullets) > 4:
            corrected['experience'][i]['descrition_list'] = bullets[:4]
            print(f"   Trimmed experience {i} bullets to 4")
    
    # Restore minimum if too few
    if len(corrected.get('experience',[])) < 2 and len(original_profile.get('experience',[])) >= 2:
        corrected['experience'] = original_profile['experience'][:2]
        print("   Restored minimum 2 experiences")
    
    if len(corrected.get('projects',[])) < 3 and len(original_profile.get('projects',[])) >= 3:
        corrected['projects'] = original_profile['projects'][:3]
        print("   Restored minimum 3 projects")
    
    # Preserve education
    if not corrected.get('education'):
        corrected['education'] = original_profile.get('education',[])
    
    return corrected


def _clean_json(content: str) -> str:
    """Clean markdown from LLM output."""
    if content.startswith("```json"):
        content = content.split("```json", 1)[1]
    elif content.startswith("```"):
        content = content.split("```", 1)[1]
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]
    return content.strip()


def generate_optimized_profile(profile: dict, job_info: dict, model_name: str) -> dict:
    """Generate optimized CV."""
    prompt_template = load_prompt("cv_optimization")
    prompt = prompt_template.format(
        profile=json.dumps(profile, indent=2, ensure_ascii=False),
        job_info=json.dumps(job_info, indent=2, ensure_ascii=False)
    )
    
    output = replicate.run(model_name, input={"prompt": prompt})
    content = "".join([str(x) for x in output]).strip()
    content = _clean_json(content)
    
    return json.loads(content)


def extract_relevant_job_info(job_raw_text: str, model_name: str) -> dict:
    """Extract job posting info."""
    clean_text = re.sub(r'\s+', ' ', job_raw_text).strip()
    prompt_template = load_prompt("job_extraction")
    prompt = prompt_template.replace("{job_text}", clean_text)
    
    output = replicate.run(model_name, input={"prompt": prompt})
    content = "".join([str(x) for x in output]).strip()
    content = _clean_json(content)
    
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {
            "title": "", "company": "", "location": "",
            "summary": clean_text,
            "requirements": [], "responsibilities": [], "keywords": []
        }
    
    # Post-process
    parsed['keywords'] = sorted(list(dict.fromkeys(parsed.get('keywords',[]))))
    for field in ['requirements', 'responsibilities']:
        if not isinstance(parsed.get(field), list):
            parsed[field] = []
    
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
    
    prompt_template = load_prompt("cv_extraction")
    prompt = prompt_template.format(cv_text=cv_text)
    
    output = replicate.run(model_name, input={"prompt": prompt})
    content = "".join([str(x) for x in output]).strip()
    content = _clean_json(content)
    
    return json.loads(content)
    
    # content = "".join([str(x) for x in output]).strip()
    
    # # Clean up potential markdown formatting
    # if content.startswith("```json"):
    #     content = content.split("```json")[1]
    # if content.startswith("```"):
    #     content = content.split("```")[1]
    # if content.endswith("```"):
    #     content = content.rsplit("```", 1)[0]
    # content = content.strip()
    
    # # Parse JSON
    # try:
    #     cv_data = json.loads(content)
    # except json.JSONDecodeError as e:
    #     raise ValueError(f"LLM did not return valid JSON. Error: {str(e)}\n\nReceived content:\n{content[:500]}...")
    
    # # Validate required fields
    # required_fields = ["personal_info", "summary", "education", "experience", "projects", "skills"]
    # for field in required_fields:
    #     if field not in cv_data:
    #         raise ValueError(f"Missing required field in extracted data: {field}")
    
    # print("✓ Successfully extracted and formatted CV data\n")
    # return cv_data


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