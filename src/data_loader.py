import json
from typing import Dict, Any, List


def normalize_profile_structure(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize profile structure to handle different input formats.
    
    Handles:
    1. PDF extraction format (work_experience, nested skills)
    2. Manual JSON format (experience, flat skills)
    3. Mixed formats
    """
    normalized = profile.copy()
    
    # Fix 1: work_experience → experience
    if 'work_experience' in normalized and 'experience' not in normalized:
        normalized['experience'] = normalized.pop('work_experience')
        print("  🔄 Normalized: work_experience → experience")
    
    # Fix 2: Flatten nested skills structure
    if 'skills' in normalized and isinstance(normalized['skills'], dict):
        # Skills is nested: {"coding": [...], "soft": [...], "hard": [...]}
        all_skills = []
        for category, skill_list in normalized['skills'].items():
            if isinstance(skill_list, list):
                all_skills.extend(skill_list)
        
        normalized['skills'] = all_skills
        print(f"  🔄 Normalized: Flattened {len(all_skills)} skills from nested structure")
    
    # Fix 3: Normalize experience field names (for template compatibility)
    if 'experience' in normalized:
        for exp in normalized['experience']:
            # job_title → title
            if 'job_title' in exp and 'title' not in exp:
                exp['title'] = exp.pop('job_title')
            
            # company_name → company
            if 'company_name' in exp and 'company' not in exp:
                exp['company'] = exp.pop('company_name')
            
            # date/dates/period → years (template expects "years"!)
            if 'date' in exp and 'years' not in exp:
                exp['years'] = exp.pop('date')
            elif 'dates' in exp and 'years' not in exp:
                exp['years'] = exp.pop('dates')
            elif 'period' in exp and 'years' not in exp:
                exp['years'] = exp.pop('period')
            
            # description_list → descrition_list (match existing typo for compatibility)
            if 'description_list' in exp and 'descrition_list' not in exp:
                exp['descrition_list'] = exp.pop('description_list')
    
    # Fix 4: Normalize project field names (for template compatibility)
    if 'projects' in normalized:
        for proj in normalized['projects']:
            # project_name → name
            if 'project_name' in proj and 'name' not in proj:
                proj['name'] = proj.pop('project_name')
            
            # date/dates/period → year (template expects "year" singular!)
            if 'date' in proj and 'year' not in proj:
                proj['year'] = proj.pop('date')
            elif 'dates' in proj and 'year' not in proj:
                proj['year'] = proj.pop('dates')
            elif 'period' in proj and 'year' not in proj:
                proj['year'] = proj.pop('period')
            
            # Projects use "description" (STRING, no typo!) NOT "descrition_list"!
            # If we have descrition_list (array), convert to single string
            if 'descrition_list' in proj and 'description' not in proj:
                proj['description'] = ' '.join(proj.pop('descrition_list'))
            elif 'description_list' in proj and 'description' not in proj:
                proj['description'] = ' '.join(proj.pop('description_list'))
    
    # Fix 5: Normalize education field names (for template compatibility)
    if 'education' in normalized:
        for edu in normalized['education']:
            # date/dates/period → year (template expects "year"!)
            if 'date' in edu and 'year' not in edu:
                edu['year'] = edu.pop('date')
            elif 'dates' in edu and 'year' not in edu:
                edu['year'] = edu.pop('dates')
            elif 'period' in edu and 'year' not in edu:
                edu['year'] = edu.pop('period')
            
            # Education uses "description" (STRING, no typo!) NOT "descrition_list"!
            # If we have descrition_list (array), convert to single string
            if 'descrition_list' in edu and 'description' not in edu:
                edu['description'] = ' '.join(edu.pop('descrition_list'))
            elif 'description_list' in edu and 'description' not in edu:
                edu['description'] = ' '.join(edu.pop('description_list'))
    
    return normalized


def load_profile(path: str) -> dict:
    """
    Load the candidate profile from JSON file.
    
    Automatically normalizes structure to handle:
    - PDF extraction format (work_experience, nested skills)
    - Manual JSON format (experience, flat skills)
    """
    with open(path, "r", encoding="utf-8") as f:
        profile = json.load(f)
    
    # Normalize structure to standard format
    profile = normalize_profile_structure(profile)
    
    return profile
