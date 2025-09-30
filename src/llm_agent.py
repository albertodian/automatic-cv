import json
import ollama
import re

def generate_optimized_profile(profile: dict, job_info: dict, model_name: str) -> dict:
    """
    Use Ollama model (default gpt-oss:20b) to generate an optimized CV profile for the job posting.
    Expects job_info to be a dict returned from extract_relevant_job_info().
    """

    prompt = f"""
        You are an expert in CV optimization for Applicant Tracking Systems (ATS).

        Candidate profile (JSON):
        {json.dumps(profile, indent=2, ensure_ascii=False)}

        Job posting information (JSON):
        {json.dumps(job_info, indent=2, ensure_ascii=False)}

        Task:
        - Return a JSON object representing the optimized CV.
        - Select the most relevant skills and experience from the candidate profile.
        - Rewrite the summary to highlight relevance to the job posting.
        - **Explicitly include the 'keywords' from the job_info JSON verbatim** wherever APPROPRIATE in skills, summary, experience or projects.
        - Do NOT invent new skills or experience not in the candidate profile.
        - Keep the format consistent with the input profile (sections, skills, education, etc.).
        - Ensure the result is valid JSON.
        """

    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}]
    )

    content = response["message"]["content"]

    # Extract the JSON block (between ```json ... ```)
    match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    if not match:
        raise ValueError("No JSON block found in response:\n" + content)

    json_str = match.group(1).strip()

    try:
        optimized_cv = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON extracted:\n{json_str}") from e

    # Explanation = everything outside the JSON block
    explanation = re.sub(r"```json.*?```", "", content, flags=re.DOTALL).strip()

    return optimized_cv, explanation



def generate_cover_letter(profile: dict, job_text: str, model_name: str) -> str:
    """
    Generate a short tailored cover letter using the LLM.
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
    
    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}]
    )

    content = response['message']['content']
    return content


def extract_relevant_job_info(job_raw_text: str, model_name: str) -> dict:
    """
    Extract and summarize a job posting into structured JSON.
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

    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}]
    )

    content = response['message']['content'].strip()

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