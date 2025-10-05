"""
Structure Validator - Ensures CV JSON structure matches template requirements

This module provides validation and correction utilities to ensure the CV JSON
matches the exact structure expected by the HTML templates.

CRITICAL: Templates expect specific field names (some with intentional typos!)
"""

import copy
from typing import Dict, Any, List, Tuple


def validate_structure(profile: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate CV structure against template requirements.
    
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check required top-level fields
    required_fields = ['personal_info', 'summary', 'education', 'experience', 'projects', 'skills']
    for field in required_fields:
        if field not in profile:
            issues.append(f"Missing required field: {field}")
    
    # Validate experience structure
    if 'experience' in profile:
        for i, exp in enumerate(profile['experience']):
            # Check for correct date field name
            if 'date' in exp and 'years' not in exp:
                issues.append(f"Experience[{i}]: Has 'date' but should be 'years' (plural)")
            if 'period' in exp and 'years' not in exp:
                issues.append(f"Experience[{i}]: Has 'period' but should be 'years'")
            if 'dates' in exp and 'years' not in exp:
                issues.append(f"Experience[{i}]: Has 'dates' but should be 'years'")
            
            # Check for correct description field (with typo!)
            if 'description_list' in exp and 'descrition_list' not in exp:
                issues.append(f"Experience[{i}]: Has 'description_list' but should be 'descrition_list' (with typo!)")
            
            # Check if descrition_list is actually an array
            if 'descrition_list' in exp and not isinstance(exp['descrition_list'], list):
                issues.append(f"Experience[{i}]: 'descrition_list' must be an array, not {type(exp['descrition_list'])}")
    
    # Validate projects structure
    if 'projects' in profile:
        for i, proj in enumerate(profile['projects']):
            # Check for correct date field name (singular!)
            if 'date' in proj and 'year' not in proj:
                issues.append(f"Project[{i}]: Has 'date' but should be 'year' (singular)")
            if 'dates' in proj and 'year' not in proj:
                issues.append(f"Project[{i}]: Has 'dates' but should be 'year' (singular)")
            if 'period' in proj and 'year' not in proj:
                issues.append(f"Project[{i}]: Has 'period' but should be 'year'")
            
            # Check for correct description field (NO typo for projects!)
            if 'descrition_list' in proj and 'description' not in proj:
                issues.append(f"Project[{i}]: Has 'descrition_list' but should be 'description' (string, no typo!)")
            
            # Check if description is a string
            if 'description' in proj and not isinstance(proj['description'], str):
                issues.append(f"Project[{i}]: 'description' must be a string, not {type(proj['description'])}")
    
    # Validate education structure
    if 'education' in profile:
        for i, edu in enumerate(profile['education']):
            # Check for correct date field name (singular!)
            if 'date' in edu and 'year' not in edu:
                issues.append(f"Education[{i}]: Has 'date' but should be 'year' (singular)")
            if 'dates' in edu and 'year' not in edu:
                issues.append(f"Education[{i}]: Has 'dates' but should be 'year' (singular)")
            if 'period' in edu and 'year' not in edu:
                issues.append(f"Education[{i}]: Has 'period' but should be 'year'")
            
            # Education uses 'description' (string, no typo!)
            if 'descrition_list' in edu and 'description' not in edu:
                issues.append(f"Education[{i}]: Has 'descrition_list' but should be 'description' (string, no typo!)")
    
    is_valid = len(issues) == 0
    return is_valid, issues


def fix_structure(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Automatically fix common structure issues.
    
    This is the DEFINITIVE structure fixer that should be called after every LLM generation.
    """
    profile = copy.deepcopy(profile)
    
    # Fix experience
    if 'experience' in profile:
        for exp in profile['experience']:
            # Fix date field names → years (plural)
            if 'date' in exp:
                exp['years'] = exp.pop('date')
            elif 'period' in exp:
                exp['years'] = exp.pop('period')
            elif 'dates' in exp:
                exp['years'] = exp.pop('dates')
            
            # Fix description_list → descrition_list (typo required!)
            if 'description_list' in exp:
                exp['descrition_list'] = exp.pop('description_list')
            
            # Ensure descrition_list is an array
            if 'descrition_list' in exp and not isinstance(exp['descrition_list'], list):
                exp['descrition_list'] = [str(exp['descrition_list'])]
    
    # Fix projects
    if 'projects' in profile:
        for proj in profile['projects']:
            # Fix date field names → year (singular)
            if 'date' in proj:
                proj['year'] = proj.pop('date')
            elif 'dates' in proj:
                proj['year'] = proj.pop('dates')
            elif 'period' in proj:
                proj['year'] = proj.pop('period')
            
            # Convert descrition_list (array) → description (string)
            if 'descrition_list' in proj and 'description' not in proj:
                if isinstance(proj['descrition_list'], list):
                    proj['description'] = ' '.join(proj.pop('descrition_list'))
                else:
                    proj['description'] = str(proj.pop('descrition_list'))
            
            # Convert description_list (array) → description (string)
            elif 'description_list' in proj and 'description' not in proj:
                if isinstance(proj['description_list'], list):
                    proj['description'] = ' '.join(proj.pop('description_list'))
                else:
                    proj['description'] = str(proj.pop('description_list'))
            
            # Ensure description is a string
            if 'description' in proj and not isinstance(proj['description'], str):
                proj['description'] = str(proj['description'])
    
    # Fix education
    if 'education' in profile:
        for edu in profile['education']:
            # Fix date field names → year (singular)
            if 'date' in edu:
                edu['year'] = edu.pop('date')
            elif 'dates' in edu:
                edu['year'] = edu.pop('dates')
            elif 'period' in edu:
                edu['year'] = edu.pop('period')
            
            # Convert descrition_list (array) → description (string)
            if 'descrition_list' in edu and 'description' not in edu:
                if isinstance(edu['descrition_list'], list):
                    edu['description'] = ' '.join(edu.pop('descrition_list'))
                else:
                    edu['description'] = str(edu.pop('descrition_list'))
            
            # Convert description_list (array) → description (string)
            elif 'description_list' in edu and 'description' not in edu:
                if isinstance(edu['description_list'], list):
                    edu['description'] = ' '.join(edu.pop('description_list'))
                else:
                    edu['description'] = str(edu.pop('description_list'))
            
            # Ensure description is a string if present
            if 'description' in edu and not isinstance(edu['description'], str):
                edu['description'] = str(edu['description'])
    
    return profile


def ensure_entries_preserved(
    new_profile: Dict[str, Any],
    original_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Ensure all entries from original profile are preserved in new profile.
    
    If entries were removed, restore them from original.
    """
    new_profile = copy.deepcopy(new_profile)
    
    # Check experiences
    orig_exp_count = len(original_profile.get('experience', []))
    new_exp_count = len(new_profile.get('experience', []))
    
    if new_exp_count < orig_exp_count:
        print(f"⚠️  {orig_exp_count - new_exp_count} experiences were removed! Restoring...")
        new_profile['experience'] = original_profile['experience']
    
    # Check projects
    orig_proj_count = len(original_profile.get('projects', []))
    new_proj_count = len(new_profile.get('projects', []))
    
    if new_proj_count < orig_proj_count:
        print(f"⚠️  {orig_proj_count - new_proj_count} projects were removed! Restoring...")
        new_profile['projects'] = original_profile['projects']
    
    # Check education
    orig_edu_count = len(original_profile.get('education', []))
    new_edu_count = len(new_profile.get('education', []))
    
    if new_edu_count < orig_edu_count:
        print(f"⚠️  {orig_edu_count - new_edu_count} education entries were removed! Restoring...")
        new_profile['education'] = original_profile['education']
    
    return new_profile


def print_validation_report(profile: Dict[str, Any]) -> None:
    """Print a validation report for the CV structure."""
    is_valid, issues = validate_structure(profile)
    
    print("\n" + "="*70)
    print("📋 CV STRUCTURE VALIDATION REPORT")
    print("="*70)
    
    if is_valid:
        print("✅ Structure is valid!")
    else:
        print(f"❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"   • {issue}")
    
    # Count entries
    exp_count = len(profile.get('experience', []))
    proj_count = len(profile.get('projects', []))
    edu_count = len(profile.get('education', []))
    skill_count = len(profile.get('skills', []))
    
    print(f"\n📊 Content Summary:")
    print(f"   • Experiences: {exp_count}")
    print(f"   • Projects: {proj_count}")
    print(f"   • Education: {edu_count}")
    print(f"   • Skills: {skill_count}")
    print("="*70 + "\n")
