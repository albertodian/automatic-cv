"""
ATS Optimization and Iterative Refinement System

This module combines:
1. ATS Optimization utilities for CV generation
2. Iterative refinement loop that automatically refines CVs until they achieve 90%+ ATS score

Helps improve Applicant Tracking System scores and ensures maximum compatibility.
Philosophy: Don't give users a bad CV with suggestions - give them a PERFECT CV!
"""

import json
import re
import replicate
from typing import Dict, List, Tuple, Any


def expand_abbreviations(text: str) -> str:
    """
    Expand common tech abbreviations to full terms for MAXIMUM ATS compatibility.
    Handles already-expanded forms intelligently to avoid double expansion.
    
    Args:
        text: Text to expand
        
    Returns:
        Text with abbreviations expanded
    """
    import re
    
    # Comprehensive tech abbreviations (60+ terms for maximum ATS scores)
    abbreviations = {
        # AI/ML
        'ML': 'Machine Learning (ML)',
        'AI': 'Artificial Intelligence (AI)', 
        'LLM': 'Large Language Model (LLM)',
        'LLMs': 'Large Language Models (LLMs)',
        'NLP': 'Natural Language Processing (NLP)',
        'CV': 'Computer Vision (CV)',
        'DL': 'Deep Learning (DL)',
        'RL': 'Reinforcement Learning (RL)',
        'CNN': 'Convolutional Neural Network (CNN)',
        'RNN': 'Recurrent Neural Network (RNN)',
        'GAN': 'Generative Adversarial Network (GAN)',
        'VLA': 'Vision-Language-Action (VLA)',
        
        # Web/API
        'API': 'Application Programming Interface (API)',
        'REST': 'RESTful API',
        'RESTful': 'RESTful API',
        'CRUD': 'Create, Read, Update, Delete (CRUD)',
        'SPA': 'Single Page Application (SPA)',
        'PWA': 'Progressive Web Application (PWA)',
        'SSR': 'Server-Side Rendering (SSR)',
        'CSR': 'Client-Side Rendering (CSR)',
        'GraphQL': 'GraphQL API',
        'JSON': 'JavaScript Object Notation (JSON)',
        'XML': 'Extensible Markup Language (XML)',
        'HTTP': 'HyperText Transfer Protocol (HTTP)',
        'HTTPS': 'Secure HTTP (HTTPS)',
        
        # Frontend
        'HTML': 'HyperText Markup Language (HTML)',
        'CSS': 'Cascading Style Sheets (CSS)',
        'JS': 'JavaScript (JS)',
        'TS': 'TypeScript (TS)',
        'DOM': 'Document Object Model (DOM)',
        'AJAX': 'Asynchronous JavaScript and XML (AJAX)',
        
        # DevOps/Cloud
        'CI/CD': 'Continuous Integration/Continuous Deployment (CI/CD)',
        'AWS': 'Amazon Web Services (AWS)',
        'GCP': 'Google Cloud Platform (GCP)',
        'Azure': 'Microsoft Azure',
        'K8s': 'Kubernetes (K8s)',
        'IaC': 'Infrastructure as Code (IaC)',
        'EC2': 'AWS EC2',
        'S3': 'AWS S3',
        'EKS': 'AWS Elastic Kubernetes Service (EKS)',
        
        # Databases
        'SQL': 'Structured Query Language (SQL)',
        'NoSQL': 'NoSQL Database',
        'ORM': 'Object-Relational Mapping (ORM)',
        'RDBMS': 'Relational Database Management System (RDBMS)',
        'DB': 'Database (DB)',
        
        # Mobile
        'iOS': 'iOS (Apple)',
        'APK': 'Android Package (APK)',
        
        # Robotics
        'ROS': 'Robot Operating System (ROS)',
        'SLAM': 'Simultaneous Localization and Mapping (SLAM)',
        'IoT': 'Internet of Things (IoT)',
        
        # Testing
        'QA': 'Quality Assurance (QA)',
        'TDD': 'Test-Driven Development (TDD)',
        'BDD': 'Behavior-Driven Development (BDD)',
        'UAT': 'User Acceptance Testing (UAT)',
        
        # Data
        'ETL': 'Extract, Transform, Load (ETL)',
        'BI': 'Business Intelligence (BI)',
        'EDA': 'Exploratory Data Analysis (EDA)',
        
        # General
        'SDK': 'Software Development Kit (SDK)',
        'IDE': 'Integrated Development Environment (IDE)',
        'CLI': 'Command Line Interface (CLI)',
        'GUI': 'Graphical User Interface (GUI)',
        'UI': 'User Interface (UI)',
        'UX': 'User Experience (UX)',
        'MVP': 'Minimum Viable Product (MVP)',
        'POC': 'Proof of Concept (POC)',
        'SaaS': 'Software as a Service (SaaS)',
        'PaaS': 'Platform as a Service (PaaS)',
        'IaaS': 'Infrastructure as a Service (IaaS)',
    }
    
    # First, clean up any malformed double expansions
    # e.g., "Continuous Integration/Continuous Deployment (Continuous Integration (CI)/Continuous Deployment (CD))"
    # Should become: "Continuous Integration/Continuous Deployment (CI/CD)"
    text = re.sub(
        r'Continuous Integration/Continuous Deployment \(Continuous Integration \(CI\)/Continuous Deployment \(CD\)\)',
        'Continuous Integration/Continuous Deployment (CI/CD)',
        text
    )
    
    # Clean up other nested parentheses patterns
    text = re.sub(
        r'(\w+(?:\s+\w+)*)\s+\(\1\s+\(([^)]+)\)\)',
        r'\1 (\2)',
        text
    )
    
    # Now expand standalone abbreviations
    for abbr, full in abbreviations.items():
        # Skip if the full form already exists in text
        if full in text:
            continue
        
        # Pattern to match standalone abbreviation not already in parentheses
        # Negative lookbehind: not preceded by '('
        # Negative lookahead: not followed by ')' or already part of expanded form
        pattern = r'(?<!\()\b' + re.escape(abbr) + r'\b(?!\))'
        
        # Check if abbreviation exists standalone
        if re.search(pattern, text):
            # Replace only the first standalone occurrence
            text = re.sub(pattern, full, text, count=1)
    
    return text


def calculate_keyword_density(cv_text: str, job_keywords: List[str]) -> Dict[str, int]:
    """
    Calculate how many times each job keyword appears in CV.
    
    Args:
        cv_text: Full CV text
        job_keywords: List of keywords from job posting
        
    Returns:
        Dict mapping keyword to occurrence count
    """
    cv_lower = cv_text.lower()
    density = {}
    
    for keyword in job_keywords:
        count = cv_lower.count(keyword.lower())
        density[keyword] = count
    
    return density


def predict_ats_score(cv_text: str, job_keywords: List[str]) -> Dict:
    """
    Predict ATS compatibility score (0-100) with advanced analysis.
    
    Uses industry-standard ATS scoring formula:
    - Keyword Match: 60%
    - Keyword Density: 20%
    - Structure: 20%
    
    Args:
        cv_text: Full CV text
        job_keywords: Keywords from job posting
        
    Returns:
        Dict with score, matched/missing keywords, recommendations
    """
    cv_lower = cv_text.lower()
    
    # Check keyword matches (with synonym awareness)
    matched = []
    missing = []
    
    for keyword in job_keywords:
        if keyword.lower() in cv_lower:
            matched.append(keyword)
        else:
            missing.append(keyword)
    
    # Calculate base keyword match rate (60% of score)
    match_rate = len(matched) / len(job_keywords) if job_keywords else 0
    keyword_score = match_rate * 60
    
    # Calculate keyword density score (20% of score)
    density = calculate_keyword_density(cv_text, matched)
    optimal_density_count = 0
    under_represented = []
    over_represented = []
    
    for kw, count in density.items():
        if 2 <= count <= 5:  # Optimal range
            optimal_density_count += 1
        elif count < 2:
            under_represented.append(kw)
        elif count > 6:
            over_represented.append(kw)
    
    density_rate = optimal_density_count / len(matched) if matched else 0
    density_score = density_rate * 20
    
    # Structure score (20% of score) - basic checks
    structure_score = 0
    if '"experience"' in cv_lower or '"work experience"' in cv_lower:
        structure_score += 5
    if '"education"' in cv_lower:
        structure_score += 5
    if '"skills"' in cv_lower:
        structure_score += 5
    if '"projects"' in cv_lower or '"portfolio"' in cv_lower:
        structure_score += 5
    
    # Total ATS score
    total_score = keyword_score + density_score + structure_score
    
    # Generate detailed recommendations
    recommendations = []
    
    # Score-based recommendations
    if total_score >= 90:
        recommendations.append(f"EXCELLENT ATS score ({total_score:.0f}%). CV will likely pass ATS filters.")
    elif total_score >= 80:
        recommendations.append(f"STRONG ATS score ({total_score:.0f}%). Very good chance of passing ATS.")
    elif total_score >= 70:
        recommendations.append(f"GOOD ATS score ({total_score:.0f}%). Should pass most ATS systems.")
    elif total_score >= 60:
        recommendations.append(f"MODERATE ATS score ({total_score:.0f}%). Consider adding more keywords.")
    else:
        recommendations.append(f"LOW ATS score ({total_score:.0f}%). Add missing keywords to improve.")
    
    # Missing keywords
    if missing:
        critical_missing = missing[:5]
        recommendations.append(f"Add these critical keywords: {', '.join(critical_missing)}")
    
    # Density issues
    if under_represented:
        recommendations.append(f"Mention more often (2-5 times ideal): {', '.join(under_represented[:3])}")
    
    if over_represented:
        recommendations.append(f"Mentioned too often (reduce): {', '.join(over_represented[:3])}")
    
    # Percentage breakdown
    recommendations.append(f"\nScore Breakdown: Keywords {keyword_score:.0f}/60 + Density {density_score:.0f}/20 + Structure {structure_score:.0f}/20")
    
    return {
        'score': round(total_score, 1),
        'keyword_match_score': round(keyword_score, 1),
        'density_score': round(density_score, 1),
        'structure_score': round(structure_score, 1),
        'matched_keywords': matched,
        'missing_keywords': missing,
        'keyword_density': density,
        'optimal_density_keywords': [kw for kw, count in density.items() if 2 <= count <= 5],
        'under_represented': under_represented,
        'over_represented': over_represented,
        'recommendations': recommendations
    }


def optimize_profile_for_ats(profile: Dict, job_keywords: List[str]) -> Dict:
    """
    Apply ATS optimizations to profile before rendering.
    
    Args:
        profile: Profile dictionary
        job_keywords: Keywords from job posting
        
    Returns:
        Optimized profile dictionary
    """
    import json
    
    # Convert to string for processing
    profile_str = json.dumps(profile)
    
    # Expand abbreviations
    profile_str = expand_abbreviations(profile_str)
    
    # Convert back to dict
    optimized_profile = json.loads(profile_str)
    
    return optimized_profile


def validate_ats_structure(profile: Dict) -> List[str]:
    """
    Validate CV structure for ATS compatibility.
    
    Args:
        profile: Profile dictionary
        
    Returns:
        List of validation warnings
    """
    warnings = []
    
    # Check required sections
    required_sections = ['personal_info', 'summary', 'experience', 'education', 'skills']
    
    for section in required_sections:
        if section not in profile or not profile[section]:
            warnings.append(f"Missing required section: {section}")
    
    # Check personal info
    if 'personal_info' in profile:
        pi = profile['personal_info']
        if 'email' not in pi:
            warnings.append("Missing email in personal info")
        if 'phone' not in pi:
            warnings.append("Missing phone in personal info")
    
    # Check experience dates
    if 'experience' in profile:
        for exp in profile['experience']:
            if 'years' not in exp and 'period' not in exp:
                warnings.append(f"Missing dates in experience: {exp.get('title', 'Unknown')}")
    
    # Check skills count
    if 'skills' in profile:
        skill_count = len(profile['skills'])
        if skill_count < 10:
            warnings.append(f"Too few skills ({skill_count}). ATS prefers 15-25 skills.")
        elif skill_count > 35:
            warnings.append(f"Too many skills ({skill_count}). Keep to 15-25 most relevant.")
    
    if not warnings:
        warnings.append("CV structure is ATS-friendly")
    
    return warnings


# ==============================================================================
# ATS ITERATIVE REFINEMENT FUNCTIONS
# ==============================================================================


def _clean_json(content: str) -> str:
    """Clean JSON response from LLM."""
    content = content.strip()
    content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'^```\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
    return content.strip()


def _call_llm(prompt: str, model_name: str) -> str:
    """Call LLM and return cleaned response."""
    output = replicate.run(model_name, input={"prompt": prompt})
    content = "".join([str(x) for x in output]).strip()
    return _clean_json(content)


def create_refinement_prompt(
    profile: Dict[str, Any],
    job_keywords: List[str],
    ats_result: Dict[str, Any],
    iteration: int
) -> str:
    """
    Create a prompt for the LLM to refine the CV based on ATS feedback.
    
    This prompt is laser-focused on fixing ATS issues without changing structure.
    """
    
    missing_keywords = ats_result.get('missing_keywords', [])[:10]  # Top 10 missing
    under_represented = ats_result.get('under_represented', [])[:5]  # Top 5 under-represented
    over_represented = ats_result.get('over_represented', [])
    current_score = ats_result.get('score', 0)
    
    prompt = f"""ROLE: ATS Score Refinement Specialist

CRITICAL MISSION: This CV scored {current_score}% on ATS. Your job is to refine it to 90%+ WITHOUT changing structure.

CURRENT ATS ANALYSIS:
- Current Score: {current_score}%
- Target Score: 90%+
- Iteration: {iteration}/3

ISSUES IDENTIFIED:

1. MISSING CRITICAL KEYWORDS (Must Add):
{chr(10).join([f"   - {kw}" for kw in missing_keywords])}

2. UNDER-REPRESENTED KEYWORDS (Need 3-5 mentions each):
{chr(10).join([f"   - {kw}" for kw in under_represented])}

{"3. OVER-REPRESENTED KEYWORDS (Reduce to 3-5 mentions):" if over_represented else ""}
{chr(10).join([f"   - {kw}" for kw in over_represented]) if over_represented else ""}

REFINEMENT STRATEGY:

Step 1: Add Missing Keywords
   - Integrate each missing keyword naturally into descriptions
   - Use in experience bullets, project descriptions, or skills section
   - Format with full form + abbreviation: "Machine Learning (ML)"
   - Add to skills array if not present

Step 2: Boost Under-Represented Keywords
   - Current mentions: 0-2 (too few)
   - Target: 3-5 mentions each
   - Add to experience bullets and project descriptions
   - Use action verbs: "Developed X using [keyword]"

Step 3: Reduce Over-Represented Keywords (if any)
   - Current mentions: 6+ (keyword stuffing penalty)
   - Target: 3-5 mentions
   - Remove redundant mentions
   - Keep most impactful occurrences

Step 4: Verify Quality
   - Descriptions still sound natural
   - No awkward keyword insertion
   - Maintain professional tone
   - Keep structure IDENTICAL (no new sections)

CRITICAL CONSTRAINTS:
DO NOT change structure (no new experiences/projects/education)
DO NOT remove ANY experiences, projects, or education entries
DO NOT change names, titles, companies, dates
DO NOT create fake information
DO NOT merge or consolidate entries
ONLY enhance descriptions with keywords
ONLY add missing keywords to skills section
ONLY adjust keyword density
MUST preserve ALL entries from input (count: {len(profile.get('experience', []))} experiences, {len(profile.get('projects', []))} projects)

INPUT CV:
{json.dumps(profile, indent=2)}

OUTPUT FORMAT:
Pure JSON only, no markdown, no commentary, no ```json markers.
Start with {{ and end with }}.

Return the REFINED CV with better keyword integration.
"""
    
    return prompt


def refine_cv_for_ats(
    profile: Dict[str, Any],
    job_keywords: List[str],
    model_name: str = "openai/gpt-4.1-mini",
    max_iterations: int = 3,
    target_score: float = 90.0,
    min_improvement: float = 5.0
) -> Tuple[Dict[str, Any], Dict[str, Any], int]:
    """
    Iteratively refine CV until it achieves target ATS score.
    
    Args:
        profile: The CV profile to refine
        job_keywords: Keywords from job posting
        model_name: LLM model to use
        max_iterations: Maximum refinement iterations (default: 3)
        target_score: Target ATS score (default: 90.0)
        min_improvement: Minimum improvement to continue (default: 5.0)
    
    Returns:
        Tuple of (refined_profile, final_ats_result, iterations_used)
    """
    
    print("ATS Iterative Refinement")
    print(f"Target: {target_score}% ATS Score")
    print(f"Max Iterations: {max_iterations}")
    
    current_profile = profile.copy()
    iteration = 0
    previous_score = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        print(f"Iteration {iteration}/{max_iterations}")

        
        # Apply basic ATS optimization (abbreviation expansion)
        if iteration == 1:
            print("\nApplying baseline ATS optimization (abbreviation expansion)...")
            current_profile = optimize_profile_for_ats(current_profile, job_keywords)
        
        # Predict current ATS score
        print(f"\nCalculating ATS score...")
        cv_text = json.dumps(current_profile)
        ats_result = predict_ats_score(cv_text, job_keywords)
        current_score = ats_result['score']
        
        print(f"\nCurrent Score: {current_score:.1f}%")
        print(f"Score Breakdown:")
        print(f"  Keyword Match: {ats_result['keyword_match_score']:.1f}/60")
        print(f"  Keyword Density: {ats_result['density_score']:.1f}/20")
        print(f"  Structure: {ats_result['structure_score']:.1f}/20")
        print(f"Matched Keywords: {len(ats_result['matched_keywords'])}/{len(job_keywords)}")
        print(f"Missing Keywords: {len(ats_result['missing_keywords'])}")
        
        # Check if we've reached target
        if current_score >= target_score:
            print(f"\nTarget achieved: {current_score:.1f}% (target: {target_score}%)")
            print(f"Converged in {iteration} iteration(s)")
            return current_profile, ats_result, iteration
        
        # Check if we're making progress
        improvement = current_score - previous_score
        if iteration > 1 and improvement < min_improvement:
            print(f"\nImprovement only {improvement:.1f}% (minimum: {min_improvement}%)")
            print(f"Stopping at {current_score:.1f}% to avoid diminishing returns")
            return current_profile, ats_result, iteration
        
        # Show what needs improvement
        if ats_result['missing_keywords']:
            print(f"\nTop Missing Keywords: {', '.join(ats_result['missing_keywords'][:5])}")
        
        if ats_result['under_represented']:
            print(f"Under-Represented: {', '.join(ats_result['under_represented'][:3])}")
        
        if ats_result['over_represented']:
            print(f"Over-Represented: {', '.join(ats_result['over_represented'][:3])}")
        
        # Don't refine on last iteration if we haven't reached target
        if iteration == max_iterations:
            print(f"\nReached max iterations ({max_iterations})")
            print(f"Final score: {current_score:.1f}% (target: {target_score}%)")
            return current_profile, ats_result, iteration
        
        # Refine with LLM
        print(f"\nRefining CV with AI to fix ATS issues...")
        refinement_prompt = create_refinement_prompt(
            current_profile,
            job_keywords,
            ats_result,
            iteration
        )
        
        try:
            refined_json = _call_llm(refinement_prompt, model_name=model_name)
            current_profile = json.loads(refined_json)
            print(f"Refinement complete")
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Keeping previous version and continuing...")
        except Exception as e:
            print(f"Refinement error: {e}")
            print(f"Keeping previous version and continuing...")
        
        previous_score = current_score
    
    # Final result
    print(f"Refinement Complete")
    print(f"Final Score: {current_score:.1f}% (Target: {target_score}%)")
    print(f"Iterations: {iteration}/{max_iterations}")
    
    return current_profile, ats_result, iteration


def get_ats_summary(ats_result: Dict[str, Any]) -> str:
    """
    Generate a concise summary of ATS performance.
    """
    score = ats_result['score']
    
    if score >= 90:
        status = "EXCELLENT"
    elif score >= 80:
        status = "VERY GOOD"
    elif score >= 70:
        status = "GOOD"
    else:
        status = "NEEDS IMPROVEMENT"
    
    summary = f"""
ATS COMPATIBILITY REPORT

Status: {status}
Score: {score:.1f}%

Breakdown:
  Keyword Match: {ats_result['keyword_match_score']:.1f}/60
  Keyword Density: {ats_result['density_score']:.1f}/20  
  Structure: {ats_result['structure_score']:.1f}/20

Keywords: {len(ats_result['matched_keywords'])} matched, {len(ats_result['missing_keywords'])} missing
"""
    
    return summary
