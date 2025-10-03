"""
CV Validation and Auto-Correction Module

This module validates the generated CV JSON and automatically fixes common issues
like page length violations, missing data, or formatting problems.
"""

import json
import re
from typing import Dict, Any, List, Tuple
from pathlib import Path
import tempfile
import os

# For page counting (optional dependencies)
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

try:
    from jinja2 import Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


class CVValidator:
    """Validates and auto-corrects CV JSON before final rendering."""
    
    def __init__(self, template_path: str = None):
        """
        Initialize the CV validator.
        
        Args:
            template_path: Path to the HTML template file for page counting
        """
        self.template_path = template_path or "templates/cv_template.html"
        self.validation_results = []
        self.auto_fixes_applied = []
    
    def validate_and_fix(self, cv_data: Dict[str, Any], 
                        job_info: Dict[str, Any] = None,
                        max_attempts: int = 3) -> Tuple[Dict[str, Any], List[str]]:
        """
        Validate CV and apply automatic fixes.
        
        Args:
            cv_data: The CV JSON data to validate
            job_info: Job posting info for context-aware fixes
            max_attempts: Maximum number of fix attempts
            
        Returns:
            Tuple of (corrected_cv_data, list_of_issues_found)
        """
        print("🔍 Starting CV validation...")
        
        corrected_data = cv_data.copy()
        all_issues = []
        
        for attempt in range(max_attempts):
            print(f"\n📋 Validation attempt {attempt + 1}/{max_attempts}")
            
            # Reset for this attempt
            self.validation_results = []
            self.auto_fixes_applied = []
            
            # Run all validation checks
            issues = self._run_all_validations(corrected_data, job_info)
            
            if not issues:
                print("✅ All validations passed!")
                break
            
            # Apply fixes
            corrected_data = self._apply_fixes(corrected_data, issues, job_info)
            all_issues.extend(issues)
            
            if attempt == max_attempts - 1:
                print("⚠️ Maximum fix attempts reached. Some issues may remain.")
        
        return corrected_data, all_issues
    
    def _run_all_validations(self, cv_data: Dict[str, Any], 
                           job_info: Dict[str, Any] = None) -> List[Dict]:
        """Run all validation checks and return list of issues."""
        issues = []
        
        # 1. Page length validation (most important)
        issues.extend(self._validate_page_length(cv_data))
        
        # 2. Required fields validation
        issues.extend(self._validate_required_fields(cv_data))
        
        # 3. Data quality validation
        issues.extend(self._validate_data_quality(cv_data))
        
        # 4. Content limits validation
        issues.extend(self._validate_content_limits(cv_data))
        
        # 5. Format consistency validation
        issues.extend(self._validate_format_consistency(cv_data))
        
        # 6. Job alignment validation (if job_info provided)
        if job_info:
            issues.extend(self._validate_job_alignment(cv_data, job_info))
        
        return issues
    
    def _validate_page_length(self, cv_data: Dict[str, Any]) -> List[Dict]:
        """Validate that the CV will fit on one page."""
        issues = []
        
        if not WEASYPRINT_AVAILABLE or not JINJA2_AVAILABLE:
            # Fallback: estimate based on content count
            total_items = self._estimate_content_length(cv_data)
            if total_items > 50:  # Rough heuristic
                issues.append({
                    "type": "page_length",
                    "severity": "high",
                    "message": f"Estimated content too long ({total_items} items). Likely exceeds 1 page.",
                    "fix": "reduce_content"
                })
            return issues
        
        try:
            # Render and check actual page count
            page_count = self._count_rendered_pages(cv_data)
            if page_count > 1:
                issues.append({
                    "type": "page_length",
                    "severity": "high", 
                    "message": f"CV renders to {page_count} pages. Must fit on 1 page.",
                    "fix": "reduce_content",
                    "page_count": page_count
                })
        except Exception as e:
            print(f"⚠️ Could not check page count: {e}")
            # Fallback to estimation
            total_items = self._estimate_content_length(cv_data)
            if total_items > 50:
                issues.append({
                    "type": "page_length",
                    "severity": "medium",
                    "message": f"Cannot verify page count. Estimated content: {total_items} items.",
                    "fix": "reduce_content"
                })
        
        return issues
    
    def _validate_required_fields(self, cv_data: Dict[str, Any]) -> List[Dict]:
        """Validate that all required fields are present and non-empty."""
        issues = []
        
        # Check top-level structure
        required_sections = ["personal_info", "summary", "education", "experience", "projects", "skills"]
        for section in required_sections:
            if section not in cv_data:
                issues.append({
                    "type": "missing_section",
                    "severity": "high",
                    "message": f"Missing required section: {section}",
                    "fix": "add_empty_section",
                    "section": section
                })
        
        # Check personal info fields
        if "personal_info" in cv_data:
            required_personal = ["name", "email"]
            for field in required_personal:
                if not cv_data["personal_info"].get(field):
                    issues.append({
                        "type": "missing_personal_info",
                        "severity": "high",
                        "message": f"Missing required personal info: {field}",
                        "fix": "cannot_auto_fix",
                        "field": field
                    })
        
        # Check summary
        if not cv_data.get("summary", "").strip():
            issues.append({
                "type": "missing_summary",
                "severity": "medium",
                "message": "Summary is empty or missing",
                "fix": "cannot_auto_fix"
            })
        
        return issues
    
    def _validate_data_quality(self, cv_data: Dict[str, Any]) -> List[Dict]:
        """Validate data quality and consistency."""
        issues = []
        
        # Check for empty arrays that should have content
        if len(cv_data.get("experience", [])) == 0:
            issues.append({
                "type": "empty_experience",
                "severity": "high",
                "message": "No experience entries found",
                "fix": "cannot_auto_fix"
            })
        
        if len(cv_data.get("skills", [])) == 0:
            issues.append({
                "type": "empty_skills",
                "severity": "medium",
                "message": "No skills found",
                "fix": "cannot_auto_fix"
            })
        
        # Check for placeholder text
        placeholders = ["TODO", "TBD", "PLACEHOLDER", "EXAMPLE"]
        def check_placeholders(obj, path=""):
            if isinstance(obj, str):
                for placeholder in placeholders:
                    if placeholder.lower() in obj.lower():
                        issues.append({
                            "type": "placeholder_text",
                            "severity": "medium",
                            "message": f"Placeholder text found at {path}: {obj[:50]}...",
                            "fix": "remove_placeholder",
                            "path": path,
                            "text": obj
                        })
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    check_placeholders(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_placeholders(item, f"{path}[{i}]")
        
        check_placeholders(cv_data)
        
        return issues
    
    def _validate_content_limits(self, cv_data: Dict[str, Any]) -> List[Dict]:
        """Validate content doesn't exceed recommended limits."""
        issues = []
        
        # Check experience count
        experiences = cv_data.get("experience", [])
        if len(experiences) > 3:
            issues.append({
                "type": "too_many_experiences",
                "severity": "high",
                "message": f"Too many experiences ({len(experiences)}). Maximum 3 for 1-page CV.",
                "fix": "reduce_experiences",
                "count": len(experiences)
            })
        
        # Check project count
        projects = cv_data.get("projects", [])
        if len(projects) > 4:
            issues.append({
                "type": "too_many_projects",
                "severity": "high",
                "message": f"Too many projects ({len(projects)}). Maximum 4 for 1-page CV.",
                "fix": "reduce_projects",
                "count": len(projects)
            })
        
        # Check description list lengths
        for i, exp in enumerate(experiences):
            desc_list = exp.get("descrition_list", [])
            if len(desc_list) > 4:
                issues.append({
                    "type": "long_description_list",
                    "severity": "medium",
                    "message": f"Experience {i} has {len(desc_list)} bullets. Maximum 4 recommended.",
                    "fix": "reduce_bullets",
                    "experience_index": i,
                    "count": len(desc_list)
                })
        
        # Check skills count
        skills = cv_data.get("skills", [])
        if len(skills) > 30:
            issues.append({
                "type": "too_many_skills",
                "severity": "medium",
                "message": f"Too many skills ({len(skills)}). Consider reducing to ~25.",
                "fix": "reduce_skills",
                "count": len(skills)
            })
        
        return issues
    
    def _validate_format_consistency(self, cv_data: Dict[str, Any]) -> List[Dict]:
        """Validate format consistency across the CV."""
        issues = []
        
        # Check date formats
        date_fields = []
        
        # Collect dates from education
        for edu in cv_data.get("education", []):
            if edu.get("year"):
                date_fields.append(("education", edu.get("year")))
        
        # Collect dates from experience
        for exp in cv_data.get("experience", []):
            if exp.get("years"):
                date_fields.append(("experience", exp.get("years")))
        
        # Check for inconsistent date formats
        date_patterns = []
        for source, date_str in date_fields:
            # Expected: "Mon YYYY - Mon YYYY" or "Mon YYYY"
            if not re.match(r'^[A-Z][a-z]{2} \d{4}( - [A-Z][a-z]{2} \d{4})?$', date_str):
                issues.append({
                    "type": "inconsistent_date_format",
                    "severity": "low",
                    "message": f"Inconsistent date format in {source}: {date_str}",
                    "fix": "fix_date_format",
                    "source": source,
                    "date": date_str
                })
        
        return issues
    
    def _validate_job_alignment(self, cv_data: Dict[str, Any], 
                              job_info: Dict[str, Any]) -> List[Dict]:
        """Validate alignment with job requirements."""
        issues = []
        
        # Check if critical job keywords are present
        job_keywords = job_info.get("keywords", [])
        cv_skills = cv_data.get("skills", [])
        
        if job_keywords:
            # Convert to lowercase for comparison
            cv_skills_lower = [skill.lower() for skill in cv_skills]
            missing_keywords = []
            
            for keyword in job_keywords[:5]:  # Check top 5 keywords
                if keyword.lower() not in cv_skills_lower:
                    missing_keywords.append(keyword)
            
            if missing_keywords:
                issues.append({
                    "type": "missing_job_keywords",
                    "severity": "medium",
                    "message": f"Missing important job keywords: {', '.join(missing_keywords)}",
                    "fix": "add_keywords",
                    "keywords": missing_keywords
                })
        
        return issues
    
    def _apply_fixes(self, cv_data: Dict[str, Any], issues: List[Dict], 
                    job_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Apply automatic fixes to resolve issues."""
        corrected_data = cv_data.copy()
        
        for issue in issues:
            fix_type = issue.get("fix")
            
            if fix_type == "reduce_content":
                corrected_data = self._fix_reduce_content(corrected_data, issue)
            elif fix_type == "reduce_experiences":
                corrected_data = self._fix_reduce_experiences(corrected_data, issue)
            elif fix_type == "reduce_projects":
                corrected_data = self._fix_reduce_projects(corrected_data, issue)
            elif fix_type == "reduce_bullets":
                corrected_data = self._fix_reduce_bullets(corrected_data, issue)
            elif fix_type == "reduce_skills":
                corrected_data = self._fix_reduce_skills(corrected_data, issue)
            elif fix_type == "add_keywords":
                corrected_data = self._fix_add_keywords(corrected_data, issue, job_info)
            elif fix_type == "fix_date_format":
                corrected_data = self._fix_date_format(corrected_data, issue)
            elif fix_type == "add_empty_section":
                corrected_data = self._fix_add_empty_section(corrected_data, issue)
            elif fix_type == "remove_placeholder":
                corrected_data = self._fix_remove_placeholder(corrected_data, issue)
            elif fix_type == "cannot_auto_fix":
                print(f"⚠️ Cannot auto-fix: {issue['message']}")
            
            self.auto_fixes_applied.append(f"Fixed: {issue['message']}")
        
        return corrected_data
    
    def _fix_reduce_content(self, cv_data: Dict[str, Any], issue: Dict) -> Dict[str, Any]:
        """Reduce overall content to fit one page."""
        print("🔧 Reducing content to fit one page...")
        
        # Priority order for reduction:
        # 1. Reduce number of experiences (keep most recent/relevant)
        # 2. Reduce number of projects  
        # 3. Reduce bullets per experience
        # 4. Reduce skills
        
        corrected = cv_data.copy()
        
        # 1. Limit experiences to 2-3
        experiences = corrected.get("experience", [])
        if len(experiences) > 3:
            corrected["experience"] = experiences[:3]
            print(f"   Reduced experiences from {len(experiences)} to 3")
        
        # 2. Limit projects to 3-4
        projects = corrected.get("projects", [])
        if len(projects) > 3:
            corrected["projects"] = projects[:3]
            print(f"   Reduced projects from {len(projects)} to 3")
        
        # 3. Limit bullets per experience to 3
        for i, exp in enumerate(corrected.get("experience", [])):
            desc_list = exp.get("descrition_list", [])
            if len(desc_list) > 3:
                corrected["experience"][i]["descrition_list"] = desc_list[:3]
                print(f"   Reduced bullets for experience {i} from {len(desc_list)} to 3")
        
        # 4. Limit skills to 20-25
        skills = corrected.get("skills", [])
        if len(skills) > 25:
            corrected["skills"] = skills[:25]
            print(f"   Reduced skills from {len(skills)} to 25")
        
        return corrected
    
    def _fix_reduce_experiences(self, cv_data: Dict[str, Any], issue: Dict) -> Dict[str, Any]:
        """Reduce number of experiences."""
        corrected = cv_data.copy()
        experiences = corrected.get("experience", [])
        target_count = min(3, len(experiences))
        corrected["experience"] = experiences[:target_count]
        print(f"🔧 Reduced experiences from {len(experiences)} to {target_count}")
        return corrected
    
    def _fix_reduce_projects(self, cv_data: Dict[str, Any], issue: Dict) -> Dict[str, Any]:
        """Reduce number of projects."""
        corrected = cv_data.copy()
        projects = corrected.get("projects", [])
        target_count = min(4, len(projects))
        corrected["projects"] = projects[:target_count]
        print(f"🔧 Reduced projects from {len(projects)} to {target_count}")
        return corrected
    
    def _fix_reduce_bullets(self, cv_data: Dict[str, Any], issue: Dict) -> Dict[str, Any]:
        """Reduce bullets in experience descriptions."""
        corrected = cv_data.copy()
        exp_index = issue.get("experience_index", 0)
        if exp_index < len(corrected.get("experience", [])):
            desc_list = corrected["experience"][exp_index].get("descrition_list", [])
            corrected["experience"][exp_index]["descrition_list"] = desc_list[:4]
            print(f"🔧 Reduced bullets for experience {exp_index} to 4")
        return corrected
    
    def _fix_reduce_skills(self, cv_data: Dict[str, Any], issue: Dict) -> Dict[str, Any]:
        """Reduce number of skills."""
        corrected = cv_data.copy()
        skills = corrected.get("skills", [])
        corrected["skills"] = skills[:25]
        print(f"🔧 Reduced skills from {len(skills)} to 25")
        return corrected
    
    def _fix_add_keywords(self, cv_data: Dict[str, Any], issue: Dict, 
                         job_info: Dict[str, Any]) -> Dict[str, Any]:
        """Add missing job keywords to skills."""
        corrected = cv_data.copy()
        missing_keywords = issue.get("keywords", [])
        current_skills = corrected.get("skills", [])
        
        # Add missing keywords to skills array
        for keyword in missing_keywords[:3]:  # Add max 3 keywords
            if keyword not in current_skills:
                current_skills.append(keyword)
        
        corrected["skills"] = current_skills
        print(f"🔧 Added missing keywords: {', '.join(missing_keywords[:3])}")
        return corrected
    
    def _fix_date_format(self, cv_data: Dict[str, Any], issue: Dict) -> Dict[str, Any]:
        """Fix inconsistent date formats."""
        corrected = cv_data.copy()
        # This would need more complex logic to parse and reformat dates
        print(f"🔧 Date format fix needed for: {issue.get('date')}")
        return corrected
    
    def _fix_add_empty_section(self, cv_data: Dict[str, Any], issue: Dict) -> Dict[str, Any]:
        """Add missing sections with empty data."""
        corrected = cv_data.copy()
        section = issue.get("section")
        
        defaults = {
            "personal_info": {},
            "summary": "",
            "education": [],
            "experience": [],
            "projects": [],
            "skills": []
        }
        
        if section in defaults:
            corrected[section] = defaults[section]
            print(f"🔧 Added empty section: {section}")
        
        return corrected
    
    def _fix_remove_placeholder(self, cv_data: Dict[str, Any], issue: Dict) -> Dict[str, Any]:
        """Remove placeholder text."""
        corrected = cv_data.copy()
        # This would need path-based editing
        print(f"🔧 Placeholder removal needed at: {issue.get('path')}")
        return corrected
    
    def _estimate_content_length(self, cv_data: Dict[str, Any]) -> int:
        """Estimate content length for page overflow detection."""
        total_items = 0
        
        # Count education entries
        total_items += len(cv_data.get("education", []))
        
        # Count experience entries and bullets
        for exp in cv_data.get("experience", []):
            total_items += 1  # The experience itself
            total_items += len(exp.get("descrition_list", []))
        
        # Count project entries
        total_items += len(cv_data.get("projects", []))
        
        # Count skills (approximate lines)
        skills_count = len(cv_data.get("skills", []))
        total_items += max(1, skills_count // 8)  # Assume ~8 skills per line
        
        return total_items
    
    def _count_rendered_pages(self, cv_data: Dict[str, Any]) -> int:
        """Count pages when CV is actually rendered."""
        if not WEASYPRINT_AVAILABLE or not JINJA2_AVAILABLE:
            raise Exception("weasyprint or jinja2 not available for page counting")
        
        # Read template
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Render with Jinja2
        template = Template(template_content)
        html_content = template.render(**cv_data)
        
        # Create temporary file and render with WeasyPrint
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_html_path = f.name
        
        try:
            # Render to PDF and count pages
            font_config = FontConfiguration()
            doc = HTML(filename=temp_html_path).render(font_config=font_config)
            page_count = len(doc.pages)
            return page_count
        finally:
            os.unlink(temp_html_path)


def validate_cv(cv_data: Dict[str, Any], 
               job_info: Dict[str, Any] = None,
               template_path: str = None) -> Tuple[Dict[str, Any], List[str]]:
    """
    Convenience function to validate and fix a CV.
    
    Args:
        cv_data: CV JSON data
        job_info: Job posting information (optional)
        template_path: Path to HTML template (optional)
        
    Returns:
        Tuple of (corrected_cv_data, list_of_issues)
    """
    validator = CVValidator(template_path)
    return validator.validate_and_fix(cv_data, job_info)


if __name__ == "__main__":
    # Example usage
    sample_cv = {
        "personal_info": {"name": "Test User", "email": "test@example.com"},
        "summary": "Test summary",
        "education": [],
        "experience": [],
        "projects": [],
        "skills": []
    }
    
    corrected_cv, issues = validate_cv(sample_cv)
    print("Issues found:", issues)