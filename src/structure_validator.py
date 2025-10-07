"""
Unified CV Structure Validator

This module provides comprehensive validation and auto-correction for CV JSON structure.
Use this for BOTH:
1. Validating imported CVs from PDF 
2. Validating final generated CVs

Key Features:
- Schema validation (required fields, data types)
- Template compatibility (including intentional typos like 'descrition_list')
- Content integrity (no invented experiences/projects)
- Content limits (1-page CV constraints)
- Auto-fix capabilities

CRITICAL: Templates expect specific field names (some with intentional typos!)
- Experience: 'years' (plural), 'descrition_list' (typo!)
- Projects: 'year' (singular), 'description' (string, no typo)
- Education: 'year' (singular), 'description' (string, no typo)
"""

import copy
import json
from typing import Dict, Any, List, Tuple, Optional


class CVValidationIssue:
    """Represents a single validation issue with severity and auto-fix capability."""
    
    SEVERITY_CRITICAL = "critical"  # Must fix (blocks rendering)
    SEVERITY_HIGH = "high"          # Should fix (impacts quality)
    SEVERITY_MEDIUM = "medium"      # Nice to fix (minor issues)
    SEVERITY_LOW = "low"            # Warnings only
    
    def __init__(self, issue_type: str, severity: str, message: str, **kwargs):
        self.type = issue_type
        self.severity = severity
        self.message = message
        self.metadata = kwargs
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "severity": self.severity,
            "message": self.message,
            **self.metadata
        }
    
    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.message}"


def validate_cv(
    profile: Dict[str, Any],
    original_profile: Optional[Dict[str, Any]] = None,
    strict: bool = True
) -> Tuple[bool, List[CVValidationIssue]]:
    """
    Universal CV validation function.
    
    Use this for BOTH:
    - Imported CVs from PDF (set original_profile=None)
    - Generated CVs (provide original_profile to check for invented content)
    
    Args:
        profile: The CV JSON to validate
        original_profile: Original user CV (for checking invented content). None for imports.
        strict: If True, fails on critical issues. If False, returns all issues.
    
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # 1. Schema Validation (Required Fields & Structure)
    issues.extend(_validate_schema(profile))
    
    # 2. Template Compatibility (Field Names & Types)
    issues.extend(_validate_template_compatibility(profile))
    
    # 3. Content Integrity (No Invented Data) - only if we have original
    if original_profile:
        issues.extend(_validate_content_integrity(profile, original_profile))
    
    # 4. Content Limits (1-Page Constraints)
    issues.extend(_validate_content_limits(profile))
    
    # 5. Data Quality (Completeness & Consistency)
    issues.extend(_validate_data_quality(profile))
    
    # Determine if valid
    if strict:
        is_valid = not any(i.severity == CVValidationIssue.SEVERITY_CRITICAL for i in issues)
    else:
        is_valid = len(issues) == 0
    
    return is_valid, issues


def _validate_schema(profile: Dict[str, Any]) -> List[CVValidationIssue]:
    """Validate required top-level fields exist."""
    issues = []
    required_fields = ['personal_info', 'summary', 'education', 'experience', 'projects', 'skills']
    
    for field in required_fields:
        if field not in profile:
            issues.append(CVValidationIssue(
                "missing_section",
                CVValidationIssue.SEVERITY_CRITICAL,
                f"Missing required section: {field}",
                field=field
            ))
    
    # Check personal info sub-fields
    if 'personal_info' in profile:
        pi = profile['personal_info']
        if not pi.get('name'):
            issues.append(CVValidationIssue(
                "missing_name",
                CVValidationIssue.SEVERITY_CRITICAL,
                "Missing required field: personal_info.name",
                field="name"
            ))
        if not pi.get('email'):
            issues.append(CVValidationIssue(
                "missing_email",
                CVValidationIssue.SEVERITY_HIGH,
                "Missing email in personal_info",
                field="email"
            ))
    
    # Check minimum content
    if 'experience' in profile and len(profile['experience']) == 0:
        issues.append(CVValidationIssue(
            "no_experiences",
            CVValidationIssue.SEVERITY_CRITICAL,
            "CV must have at least one experience entry",
            field="experience"
        ))
    
    if 'summary' in profile and not profile['summary'].strip():
        issues.append(CVValidationIssue(
            "empty_summary",
            CVValidationIssue.SEVERITY_HIGH,
            "Summary cannot be empty",
            field="summary"
        ))
    
    return issues


def _validate_template_compatibility(profile: Dict[str, Any]) -> List[CVValidationIssue]:
    """Validate field names and types match template expectations."""
    issues = []
    
    # Validate EXPERIENCE structure
    for i, exp in enumerate(profile.get('experience', [])):
        # Date field: must be 'years' (plural)
        if 'date' in exp or 'dates' in exp or 'period' in exp:
            if 'years' not in exp:
                issues.append(CVValidationIssue(
                    "wrong_date_field",
                    CVValidationIssue.SEVERITY_HIGH,
                    f"Experience[{i}]: Date field should be 'years' (plural)",
                    exp_index=i,
                    section="experience"
                ))
        
        # Description field: must be 'descrition_list' (typo!) and must be array
        if 'description_list' in exp and 'descrition_list' not in exp:
            issues.append(CVValidationIssue(
                "wrong_description_field",
                CVValidationIssue.SEVERITY_HIGH,
                f"Experience[{i}]: Should use 'descrition_list' (with typo!)",
                exp_index=i,
                section="experience"
            ))
        
        if 'descrition_list' in exp and not isinstance(exp['descrition_list'], list):
            issues.append(CVValidationIssue(
                "wrong_description_type",
                CVValidationIssue.SEVERITY_HIGH,
                f"Experience[{i}]: 'descrition_list' must be array",
                exp_index=i,
                section="experience"
            ))
    
    # Validate PROJECTS structure
    for i, proj in enumerate(profile.get('projects', [])):
        # Date field: must be 'year' (singular)
        if 'date' in proj or 'dates' in proj or 'period' in proj:
            if 'year' not in proj:
                issues.append(CVValidationIssue(
                    "wrong_date_field",
                    CVValidationIssue.SEVERITY_HIGH,
                    f"Project[{i}]: Date field should be 'year' (singular)",
                    proj_index=i,
                    section="projects"
                ))
        
        # Description field: must be 'description' (string, NO typo)
        if 'descrition_list' in proj and 'description' not in proj:
            issues.append(CVValidationIssue(
                "wrong_description_field",
                CVValidationIssue.SEVERITY_HIGH,
                f"Project[{i}]: Should use 'description' (string, no typo)",
                proj_index=i,
                section="projects"
            ))
        
        if 'description' in proj and not isinstance(proj['description'], str):
            issues.append(CVValidationIssue(
                "wrong_description_type",
                CVValidationIssue.SEVERITY_HIGH,
                f"Project[{i}]: 'description' must be string",
                proj_index=i,
                section="projects"
            ))
    
    # Validate EDUCATION structure
    for i, edu in enumerate(profile.get('education', [])):
        # Date field: must be 'year' (singular)
        if 'date' in edu or 'dates' in edu or 'period' in edu:
            if 'year' not in edu:
                issues.append(CVValidationIssue(
                    "wrong_date_field",
                    CVValidationIssue.SEVERITY_HIGH,
                    f"Education[{i}]: Date field should be 'year' (singular)",
                    edu_index=i,
                    section="education"
                ))
        
        # Description field: 'description' (string, if present)
        if 'descrition_list' in edu:
            issues.append(CVValidationIssue(
                "wrong_description_field",
                CVValidationIssue.SEVERITY_MEDIUM,
                f"Education[{i}]: Should use 'description' (string), not 'descrition_list'",
                edu_index=i,
                section="education"
            ))
    
    return issues


def _validate_content_integrity(
    profile: Dict[str, Any],
    original_profile: Dict[str, Any]
) -> List[CVValidationIssue]:
    """Validate no invented experiences or projects (for generated CVs)."""
    issues = []
    
    # Check for invented EXPERIENCES
    orig_exp = {(e.get('title', ''), e.get('company', '')) 
                for e in original_profile.get('experience', [])}
    out_exp = {(e.get('title', ''), e.get('company', '')) 
               for e in profile.get('experience', [])}
    invented_exp = out_exp - orig_exp
    
    for title, company in invented_exp:
        issues.append(CVValidationIssue(
            "invented_experience",
            CVValidationIssue.SEVERITY_CRITICAL,
            f"Invented experience: '{title}' at '{company}'",
            title=title,
            company=company,
            section="experience"
        ))
    
    # Check for invented PROJECTS
    orig_proj = {p.get('name', '') for p in original_profile.get('projects', [])}
    out_proj = {p.get('name', '') for p in profile.get('projects', [])}
    invented_proj = out_proj - orig_proj
    
    for name in invented_proj:
        if name:  # Skip empty names
            issues.append(CVValidationIssue(
                "invented_project",
                CVValidationIssue.SEVERITY_CRITICAL,
                f"Invented project: '{name}'",
                name=name,
                section="projects"
            ))
    
    return issues


def _validate_content_limits(profile: Dict[str, Any]) -> List[CVValidationIssue]:
    """Validate content doesn't exceed 1-page CV limits."""
    issues = []
    
    exp_count = len(profile.get('experience', []))
    proj_count = len(profile.get('projects', []))
    skill_count = len(profile.get('skills', []))
    
    # Experience limit
    if exp_count > 3:
        issues.append(CVValidationIssue(
            "too_many_experiences",
            CVValidationIssue.SEVERITY_HIGH,
            f"Too many experiences ({exp_count}). Maximum 3 for 1-page CV",
            count=exp_count,
            max=3,
            section="experience"
        ))
    
    # Project limit
    if proj_count > 4:
        issues.append(CVValidationIssue(
            "too_many_projects",
            CVValidationIssue.SEVERITY_HIGH,
            f"Too many projects ({proj_count}). Maximum 4 for 1-page CV",
            count=proj_count,
            max=4,
            section="projects"
        ))
    
    # Total items limit
    if exp_count + proj_count > 7:
        issues.append(CVValidationIssue(
            "too_much_content",
            CVValidationIssue.SEVERITY_HIGH,
            f"Too many total items ({exp_count + proj_count}). Maximum 7 (experiences + projects)",
            count=exp_count + proj_count,
            max=7
        ))
    
    # Bullets per experience
    for i, exp in enumerate(profile.get('experience', [])):
        bullets = len(exp.get('descrition_list', []))
        if bullets > 4:
            issues.append(CVValidationIssue(
                "too_many_bullets",
                CVValidationIssue.SEVERITY_MEDIUM,
                f"Experience[{i}]: Too many bullets ({bullets}). Maximum 4 recommended",
                exp_index=i,
                count=bullets,
                max=4,
                section="experience"
            ))
    
    # Skills limit
    if skill_count > 30:
        issues.append(CVValidationIssue(
            "too_many_skills",
            CVValidationIssue.SEVERITY_MEDIUM,
            f"Too many skills ({skill_count}). Consider reducing to ~25",
            count=skill_count,
            section="skills"
        ))
    elif skill_count < 10:
        issues.append(CVValidationIssue(
            "too_few_skills",
            CVValidationIssue.SEVERITY_LOW,
            f"Few skills ({skill_count}). Consider adding more (15-25 optimal)",
            count=skill_count,
            section="skills"
        ))
    
    return issues


def _validate_data_quality(profile: Dict[str, Any]) -> List[CVValidationIssue]:
    """Validate data quality and completeness."""
    issues = []
    
    # Check for placeholder text
    placeholders = ['TODO', 'TBD', 'PLACEHOLDER', 'EXAMPLE', 'XXX']
    
    def check_text(text: str, path: str):
        if text and any(ph.lower() in text.lower() for ph in placeholders):
            issues.append(CVValidationIssue(
                "placeholder_text",
                CVValidationIssue.SEVERITY_MEDIUM,
                f"Placeholder text found at {path}",
                path=path
            ))
    
    # Check summary
    check_text(profile.get('summary', ''), 'summary')
    
    # Check experiences
    for i, exp in enumerate(profile.get('experience', [])):
        check_text(exp.get('title', ''), f'experience[{i}].title')
        check_text(exp.get('company', ''), f'experience[{i}].company')
        for j, bullet in enumerate(exp.get('descrition_list', [])):
            check_text(bullet, f'experience[{i}].descrition_list[{j}]')
    
    # Check projects
    for i, proj in enumerate(profile.get('projects', [])):
        check_text(proj.get('name', ''), f'projects[{i}].name')
        check_text(proj.get('description', ''), f'projects[{i}].description')
    
    return issues


def _check_personal_info_fields(profile: Dict[str, Any]) -> List[str]:
    """
    Check which optional personal info fields are empty or missing.
    
    Only checks optional fields that users can fill via UI:
    - nationality, age, linkedin, github
    
    Critical fields (name, email, phone) are checked in schema validation.
    
    Returns:
        List of optional field names that are empty or missing (user can fill these via UI)
    """
    empty_fields = []
    personal_info = profile.get('personal_info', {})
    
    # Optional fields that can be filled via UI
    optional_fields = [
        'nationality',
        'age',
        'linkedin',
        'github'
    ]
    
    for field in optional_fields:
        value = personal_info.get(field)
        # Check if field is missing, None, or empty string
        if not value or (isinstance(value, str) and not value.strip()):
            empty_fields.append(field)
    
    return empty_fields


def fix_cv(
    profile: Dict[str, Any],
    original_profile: Optional[Dict[str, Any]] = None,
    auto_fix: bool = True
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate and auto-fix CV structure.
    
    This is the MAIN function to use for validation + fixing.
    
    Args:
        profile: CV JSON to validate/fix
        original_profile: Original CV (for checking invented content). None for imports.
        auto_fix: If True, automatically applies fixes
    
    Returns:
        Tuple of (fixed_profile, list_of_fix_messages)
    """
    profile = copy.deepcopy(profile)
    fix_messages = []
    
    # Check for empty optional personal info fields (informational only)
    empty_optional_fields = _check_personal_info_fields(profile)
    
    if not auto_fix:
        # Just validate
        is_valid, issues = validate_cv(profile, original_profile)
        messages = [str(issue) for issue in issues]
        # Add optional fields info at the end (not blocking)
        if empty_optional_fields:
            messages.append(f"INFO: Optional fields can be filled via UI: {', '.join(empty_optional_fields)}")
        return profile, messages
    
    # Validate first
    is_valid, issues = validate_cv(profile, original_profile, strict=False)
    
    if is_valid:
        # Profile is valid, just inform about optional fields
        if empty_optional_fields:
            return profile, [f"No fixes needed. Optional fields to fill: {', '.join(empty_optional_fields)}"]
        return profile, ["No fixes needed"]
    
    # Apply fixes
    for issue in issues:
        fixed, msg = _apply_single_fix(profile, issue, original_profile)
        if fixed:
            profile = fixed
            if msg:
                fix_messages.append(msg)
    
    # Ensure optional fields exist in personal_info (so UI can fill them)
    if 'personal_info' not in profile:
        profile['personal_info'] = {}
    
    optional_fields_defaults = {
        'nationality': '',
        'age': None,
        'linkedin': '',
        'github': ''
    }
    
    for field, default in optional_fields_defaults.items():
        if field not in profile['personal_info']:
            profile['personal_info'][field] = default
    
    # Re-validate
    is_valid, remaining_issues = validate_cv(profile, original_profile)
    if remaining_issues:
        for issue in remaining_issues:
            if issue.severity == CVValidationIssue.SEVERITY_CRITICAL:
                fix_messages.append(f"UNFIXED: {issue}")
    
    # Add info about optional fields at the end (informational)
    empty_optional_fields = _check_personal_info_fields(profile)
    if empty_optional_fields:
        fix_messages.append(f"INFO: Optional fields to fill via UI: {', '.join(empty_optional_fields)}")
    
    return profile, fix_messages


def _apply_single_fix(
    profile: Dict[str, Any],
    issue: CVValidationIssue,
    original_profile: Optional[Dict[str, Any]]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Apply a single fix based on issue type."""
    
    # Template compatibility fixes
    if issue.type == "wrong_date_field":
        return _fix_date_fields(profile, issue)
    
    elif issue.type == "wrong_description_field":
        return _fix_description_fields(profile, issue)
    
    elif issue.type == "wrong_description_type":
        return _fix_description_types(profile, issue)
    
    # Content integrity fixes
    elif issue.type == "invented_experience":
        return _fix_invented_experiences(profile, original_profile)
    
    elif issue.type == "invented_project":
        return _fix_invented_projects(profile, original_profile)
    
    # Content limit fixes
    elif issue.type == "too_many_experiences":
        return _fix_too_many_experiences(profile, issue)
    
    elif issue.type == "too_many_projects":
        return _fix_too_many_projects(profile, issue)
    
    elif issue.type == "too_much_content":
        return _fix_too_much_content(profile, issue)
    
    elif issue.type == "too_many_bullets":
        return _fix_too_many_bullets(profile, issue)
    
    elif issue.type == "too_many_skills":
        return _fix_too_many_skills(profile, issue)
    
    # Schema fixes
    elif issue.type == "missing_section":
        return _fix_missing_section(profile, issue)
    
    # Cannot auto-fix
    else:
        return None, None


# ==============================================================================
# INDIVIDUAL FIX FUNCTIONS
# ==============================================================================

def _fix_date_fields(profile: Dict[str, Any], issue: CVValidationIssue) -> Tuple[Dict[str, Any], str]:
    """Fix date field names to match template expectations."""
    section = issue.metadata.get('section')
    
    if section == 'experience':
        for exp in profile.get('experience', []):
            if 'date' in exp:
                exp['years'] = exp.pop('date')
            elif 'dates' in exp:
                exp['years'] = exp.pop('dates')
            elif 'period' in exp:
                exp['years'] = exp.pop('period')
        return profile, "Fixed experience date fields -> 'years'"
    
    elif section in ['projects', 'education']:
        items = profile.get(section, [])
        for item in items:
            if 'date' in item:
                item['year'] = item.pop('date')
            elif 'dates' in item:
                item['year'] = item.pop('dates')
            elif 'period' in item:
                item['year'] = item.pop('period')
        return profile, f"Fixed {section} date fields -> 'year'"
    
    return profile, None


def _fix_description_fields(profile: Dict[str, Any], issue: CVValidationIssue) -> Tuple[Dict[str, Any], str]:
    """Fix description field names to match template expectations."""
    section = issue.metadata.get('section')
    
    if section == 'experience':
        for exp in profile.get('experience', []):
            if 'description_list' in exp:
                exp['descrition_list'] = exp.pop('description_list')
        return profile, "Fixed experience description fields -> 'descrition_list' (typo)"
    
    elif section == 'projects':
        for proj in profile.get('projects', []):
            if 'descrition_list' in proj:
                # Convert array to string for projects
                if isinstance(proj['descrition_list'], list):
                    proj['description'] = ' '.join(proj.pop('descrition_list'))
                else:
                    proj['description'] = str(proj.pop('descrition_list'))
            elif 'description_list' in proj:
                if isinstance(proj['description_list'], list):
                    proj['description'] = ' '.join(proj.pop('description_list'))
                else:
                    proj['description'] = str(proj.pop('description_list'))
        return profile, "Fixed project description fields -> 'description' (string)"
    
    elif section == 'education':
        for edu in profile.get('education', []):
            if 'descrition_list' in edu:
                if isinstance(edu['descrition_list'], list):
                    edu['description'] = ' '.join(edu.pop('descrition_list'))
                else:
                    edu['description'] = str(edu.pop('descrition_list'))
            elif 'description_list' in edu:
                if isinstance(edu['description_list'], list):
                    edu['description'] = ' '.join(edu.pop('description_list'))
                else:
                    edu['description'] = str(edu.pop('description_list'))
        return profile, "Fixed education description fields -> 'description' (string)"
    
    return profile, None


def _fix_description_types(profile: Dict[str, Any], issue: CVValidationIssue) -> Tuple[Dict[str, Any], str]:
    """Fix description types (array vs string)."""
    section = issue.metadata.get('section')
    
    if section == 'experience':
        exp_index = issue.metadata.get('exp_index')
        if exp_index is not None and exp_index < len(profile.get('experience', [])):
            exp = profile['experience'][exp_index]
            if 'descrition_list' in exp and not isinstance(exp['descrition_list'], list):
                exp['descrition_list'] = [str(exp['descrition_list'])]
        return profile, f"Fixed experience[{exp_index}] description type -> array"
    
    elif section == 'projects':
        proj_index = issue.metadata.get('proj_index')
        if proj_index is not None and proj_index < len(profile.get('projects', [])):
            proj = profile['projects'][proj_index]
            if 'description' in proj and not isinstance(proj['description'], str):
                proj['description'] = str(proj['description'])
        return profile, f"Fixed project[{proj_index}] description type -> string"
    
    return profile, None


def _fix_invented_experiences(
    profile: Dict[str, Any],
    original_profile: Optional[Dict[str, Any]]
) -> Tuple[Dict[str, Any], str]:
    """Remove invented experiences."""
    if not original_profile:
        return profile, None
    
    orig_exp = {(e.get('title', ''), e.get('company', ''))
                for e in original_profile.get('experience', [])}
    valid_exp = [e for e in profile.get('experience', [])
                 if (e.get('title', ''), e.get('company', '')) in orig_exp]
    
    removed = len(profile.get('experience', [])) - len(valid_exp)
    profile['experience'] = valid_exp
    
    if removed > 0:
        return profile, f"Removed {removed} invented experience(s)"
    return profile, None


def _fix_invented_projects(
    profile: Dict[str, Any],
    original_profile: Optional[Dict[str, Any]]
) -> Tuple[Dict[str, Any], str]:
    """Remove invented projects."""
    if not original_profile:
        return profile, None
    
    orig_proj = {p.get('name', '') for p in original_profile.get('projects', [])}
    valid_proj = [p for p in profile.get('projects', [])
                  if p.get('name', '') in orig_proj]
    
    removed = len(profile.get('projects', [])) - len(valid_proj)
    profile['projects'] = valid_proj
    
    if removed > 0:
        return profile, f"Removed {removed} invented project(s)"
    return profile, None


def _fix_too_many_experiences(profile: Dict[str, Any], issue: CVValidationIssue) -> Tuple[Dict[str, Any], str]:
    """Reduce experiences to max 3."""
    experiences = profile.get('experience', [])
    if len(experiences) > 3:
        profile['experience'] = experiences[:3]
        return profile, f"Reduced experiences from {len(experiences)} to 3"
    return profile, None


def _fix_too_many_projects(profile: Dict[str, Any], issue: CVValidationIssue) -> Tuple[Dict[str, Any], str]:
    """Reduce projects to max 4."""
    projects = profile.get('projects', [])
    if len(projects) > 4:
        profile['projects'] = projects[:4]
        return profile, f"Reduced projects from {len(projects)} to 4"
    return profile, None


def _fix_too_much_content(profile: Dict[str, Any], issue: CVValidationIssue) -> Tuple[Dict[str, Any], str]:
    """Balance experiences and projects to fit 1 page."""
    experiences = profile.get('experience', [])
    projects = profile.get('projects', [])
    
    # Strategy: Keep 2-3 experiences, 3-4 projects
    if len(experiences) > 3:
        profile['experience'] = experiences[:3]
    if len(projects) > 4:
        profile['projects'] = projects[:4]
    
    # If still too much, reduce projects first
    total = len(profile['experience']) + len(profile['projects'])
    if total > 7:
        profile['projects'] = profile['projects'][:max(3, 7 - len(profile['experience']))]
    
    return profile, "Reduced total content to fit 1 page"


def _fix_too_many_bullets(profile: Dict[str, Any], issue: CVValidationIssue) -> Tuple[Dict[str, Any], str]:
    """Reduce bullets per experience to max 4."""
    exp_index = issue.metadata.get('exp_index')
    if exp_index is not None and exp_index < len(profile.get('experience', [])):
        exp = profile['experience'][exp_index]
        bullets = exp.get('descrition_list', [])
        if len(bullets) > 4:
            profile['experience'][exp_index]['descrition_list'] = bullets[:4]
            return profile, f"Reduced experience[{exp_index}] bullets from {len(bullets)} to 4"
    return profile, None


def _fix_too_many_skills(profile: Dict[str, Any], issue: CVValidationIssue) -> Tuple[Dict[str, Any], str]:
    """Reduce skills to reasonable number."""
    skills = profile.get('skills', [])
    if len(skills) > 25:
        profile['skills'] = skills[:25]
        return profile, f"Reduced skills from {len(skills)} to 25"
    return profile, None


def _fix_missing_section(profile: Dict[str, Any], issue: CVValidationIssue) -> Tuple[Dict[str, Any], str]:
    """Add missing required section."""
    field = issue.metadata.get('field')
    defaults = {
        'personal_info': {},
        'summary': '',
        'education': [],
        'experience': [],
        'projects': [],
        'skills': []
    }
    
    if field in defaults:
        profile[field] = defaults[field]
        return profile, f"Added missing section: {field}"
    return profile, None


# ==============================================================================
# LEGACY COMPATIBILITY FUNCTIONS
# ==============================================================================

def fix_structure(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Legacy function for backwards compatibility.
    Auto-fixes structure without validation reporting.
    
    This is the DEFINITIVE structure fixer that should be called after every LLM generation.
    """
    profile = copy.deepcopy(profile)
    
    # Fix experience
    if 'experience' in profile:
        for exp in profile['experience']:
            # Fix date field names to 'years' (plural)
            if 'date' in exp:
                exp['years'] = exp.pop('date')
            elif 'period' in exp:
                exp['years'] = exp.pop('period')
            elif 'dates' in exp:
                exp['years'] = exp.pop('dates')
            
            # Fix description_list to 'descrition_list' (typo required!)
            if 'description_list' in exp:
                exp['descrition_list'] = exp.pop('description_list')
            
            # Ensure descrition_list is an array
            if 'descrition_list' in exp and not isinstance(exp['descrition_list'], list):
                exp['descrition_list'] = [str(exp['descrition_list'])]
    
    # Fix projects
    if 'projects' in profile:
        for proj in profile['projects']:
            # Fix date field names to 'year' (singular)
            if 'date' in proj:
                proj['year'] = proj.pop('date')
            elif 'dates' in proj:
                proj['year'] = proj.pop('dates')
            elif 'period' in proj:
                proj['year'] = proj.pop('period')
            
            # Convert descrition_list (array) to description (string)
            if 'descrition_list' in proj and 'description' not in proj:
                if isinstance(proj['descrition_list'], list):
                    proj['description'] = ' '.join(proj.pop('descrition_list'))
                else:
                    proj['description'] = str(proj.pop('descrition_list'))
            
            # Convert description_list (array) to description (string)
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
            # Fix date field names to 'year' (singular)
            if 'date' in edu:
                edu['year'] = edu.pop('date')
            elif 'dates' in edu:
                edu['year'] = edu.pop('dates')
            elif 'period' in edu:
                edu['year'] = edu.pop('period')
            
            # Convert descrition_list (array) to description (string)
            if 'descrition_list' in edu and 'description' not in edu:
                if isinstance(edu['descrition_list'], list):
                    edu['description'] = ' '.join(edu.pop('descrition_list'))
                else:
                    edu['description'] = str(edu.pop('descrition_list'))
            
            # Convert description_list (array) to description (string)
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
        print(f"{orig_exp_count - new_exp_count} experiences were removed. Restoring...")
        new_profile['experience'] = original_profile['experience']
    
    # Check projects
    orig_proj_count = len(original_profile.get('projects', []))
    new_proj_count = len(new_profile.get('projects', []))
    
    if new_proj_count < orig_proj_count:
        print(f"{orig_proj_count - new_proj_count} projects were removed. Restoring...")
        new_profile['projects'] = original_profile['projects']
    
    # Check education
    orig_edu_count = len(original_profile.get('education', []))
    new_edu_count = len(new_profile.get('education', []))
    
    if new_edu_count < orig_edu_count:
        print(f"{orig_edu_count - new_edu_count} education entries were removed. Restoring...")
        new_profile['education'] = original_profile['education']
    
    return new_profile


def validate_structure(profile: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Legacy function for backwards compatibility.
    Use validate_cv() for new code.
    
    Returns:
        Tuple of (is_valid, list_of_issues_as_strings)
    """
    is_valid, issues = validate_cv(profile, original_profile=None, strict=True)
    issue_strings = [str(issue) for issue in issues]
    return is_valid, issue_strings


def print_validation_report(profile: Dict[str, Any]) -> None:
    """Print a validation report for the CV structure."""
    is_valid, issues = validate_cv(profile, original_profile=None, strict=True)
    
    print("\n" + "="*70)
    print("CV STRUCTURE VALIDATION REPORT")
    print("="*70)
    
    if is_valid:
        print("Structure is valid")
    else:
        print(f"Found {len(issues)} issues:")
        for issue in issues:
            print(f"  {issue}")
    
    # Count entries
    exp_count = len(profile.get('experience', []))
    proj_count = len(profile.get('projects', []))
    edu_count = len(profile.get('education', []))
    skill_count = len(profile.get('skills', []))
    
    print(f"\nContent Summary:")
    print(f"  Experiences: {exp_count}")
    print(f"  Projects: {proj_count}")
    print(f"  Education: {edu_count}")
    print(f"  Skills: {skill_count}")
    print("="*70 + "\n")


# ==============================================================================
# MAIN EXPORTS (Use these in new code)
# ==============================================================================

__all__ = [
    # New unified API (recommended)
    'validate_cv',
    'fix_cv',
    'CVValidationIssue',
    
    # Legacy API (for backwards compatibility)
    'validate_structure',
    'fix_structure',
    'ensure_entries_preserved',
    'print_validation_report',
]


# ==============================================================================
# USAGE EXAMPLES
# ==============================================================================

"""
USAGE EXAMPLES:

1. Validate and auto-fix imported CV from PDF:
   ```python
   from structure_validator import fix_cv
   
   # Load CV extracted from PDF
   imported_cv = load_cv_from_pdf("resume.pdf")
   
   # Validate and auto-fix (no original_profile needed)
   fixed_cv, messages = fix_cv(imported_cv, original_profile=None, auto_fix=True)
   
   print("\\n".join(messages))
   # Output:
   # Fixed experience date fields -> 'years'
   # Fixed project description fields -> 'description' (string)
   # Reduced experiences from 5 to 3
   ```

2. Validate and auto-fix generated CV (with integrity checks):
   ```python
   from structure_validator import fix_cv
   
   # Original user CV and LLM-generated optimized CV
   original_cv = load_profile("data/profile.json")
   generated_cv = generate_cv_with_llm(original_cv, job_info)
   
   # Validate and auto-fix (with original_profile to check for invented content)
   fixed_cv, messages = fix_cv(generated_cv, original_profile=original_cv, auto_fix=True)
   
   print("\\n".join(messages))
   # Output:
   # Removed 1 invented experience(s)
   # Fixed experience description fields -> 'descrition_list' (typo)
   # Reduced total content to fit 1 page
   ```

3. Just validate without auto-fixing:
   ```python
   from structure_validator import validate_cv
   
   is_valid, issues = validate_cv(cv_data, original_profile=None, strict=True)
   
   if not is_valid:
       for issue in issues:
           print(f"{issue.severity}: {issue.message}")
   ```

4. Integration in main pipeline:
   ```python
   # Step 1: Extract CV from PDF
   imported_cv = extract_cv_from_pdf("resume.pdf")
   
   # Step 2: Validate and fix imported CV
   from structure_validator import fix_cv
   clean_cv, _ = fix_cv(imported_cv, original_profile=None, auto_fix=True)
   
   # Step 3: Generate optimized CV
   generated_cv = generate_optimized_cv(clean_cv, job_info)
   
   # Step 4: Validate and fix generated CV (with integrity checks)
   final_cv, fix_messages = fix_cv(generated_cv, original_profile=clean_cv, auto_fix=True)
   
   # Step 5: Check ATS score (separate validation)
   from ats_optimizer import predict_ats_score
   ats_result = predict_ats_score(json.dumps(final_cv), job_keywords)
   
   # Step 6: Render to PDF (with PDF validation)
   from renderer import render_cv_pdf_html
   render_cv_pdf_html(final_cv, template="modern", output="final_cv.pdf")
   ```
"""
