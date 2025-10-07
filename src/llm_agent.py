import json
import re
import os
import copy
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


def optimize_cv_with_rag(profile: Dict[str, Any], job_info: Dict[str, Any], model_name: str) -> Dict[str, Any]:
    """
    Generate optimized CV using RAG-enhanced prompt.
    This function expects pre-filtered content from the RAG system.
    """
    # Check if RAG-specific prompt exists, otherwise fall back to standard
    try:
        prompt_template = load_prompt("cv_optimization_rag")
    except FileNotFoundError:
        print("RAG prompt not found, using standard prompt")
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
                print("Successfully extracted text directly from PDF")
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
                print("Successfully extracted text using PyMuPDF")
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
                print("Successfully extracted text using PyPDF2")
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
                print("Successfully extracted text using OCR")
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
    

# def enhance_project_descriptions(
#     profile: dict,
#     job_keywords: List[str],
#     model_name: str
# ) -> dict:
#     """
#     Enhance project descriptions to improve RAG retrieval without inventing information.
    
#     Expands technical details, adds context, and includes relevant keywords
#     to boost semantic matching while staying truthful to original content.
    
#     Args:
#         profile: CV profile with projects
#         job_keywords: Keywords from job description for context
#         model_name: Replicate model name
    
#     Returns:
#         Profile with enhanced project descriptions
#     """
#     profile = copy.deepcopy(profile)
    
#     if not profile.get('projects'):
#         return profile
    
#     prompt_template = load_prompt("project_enhancement")
#     job_keywords_str = ", ".join(job_keywords[:15])  # Top 15 keywords for context
    
#     print("Enhancing project descriptions for better RAG retrieval...")
    
#     for i, project in enumerate(profile['projects']):
#         original_desc = project.get('description', '')
        
#         if not original_desc or len(original_desc) < 20:
#             continue  # Skip very short descriptions
        
#         prompt = prompt_template.format(
#             project_name=project.get('name', 'Unknown'),
#             project_year=project.get('year', 'N/A'),
#             project_description=original_desc,
#             job_keywords=job_keywords_str
#         )
        
#         try:
#             output = replicate.run(model_name, input={"prompt": prompt})
#             enhanced_desc = "".join([str(x) for x in output]).strip()
            
#             # Clean up any markdown or extra formatting
#             enhanced_desc = enhanced_desc.replace('```', '').strip()
            
#             # Only update if we got a reasonable response
#             if len(enhanced_desc) > len(original_desc) * 0.5:  # At least 50% of original length
#                 profile['projects'][i]['description'] = enhanced_desc
#                 print(f"  Enhanced: {project.get('name', 'Unknown')}")
        
#         except Exception as e:
#             print(f"  Skipped {project.get('name', 'Unknown')}: {e}")
#             continue
    
#     return profile


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
        print(f"CV data successfully saved to {output_path}")
    except Exception as e:
        raise ValueError(f"Error saving JSON file: {str(e)}")