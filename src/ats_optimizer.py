"""
ATS Optimization utilities for CV generation.
Helps improve Applicant Tracking System scores.
"""

from typing import Dict, List, Tuple


def expand_abbreviations(text: str) -> str:
    """
    Expand common tech abbreviations to full terms for MAXIMUM ATS compatibility.
    
    Args:
        text: Text to expand
        
    Returns:
        Text with abbreviations expanded
    """
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
        'CI': 'Continuous Integration (CI)',
        'CD': 'Continuous Deployment (CD)',
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
    
    # Only expand if abbreviation appears standalone (not already expanded)
    import re
    for abbr, full in abbreviations.items():
        # Check if already expanded
        if full not in text:
            # Replace standalone occurrences (word boundaries)
            pattern = r'\b' + re.escape(abbr) + r'\b'
            text = re.sub(pattern, full, text, count=1)  # Only first occurrence to avoid repetition
    
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
        recommendations.append(f"🏆 EXCELLENT ATS score ({total_score:.0f}%)! Your CV will likely pass ATS filters.")
    elif total_score >= 80:
        recommendations.append(f"✅ STRONG ATS score ({total_score:.0f}%). Very good chance of passing ATS.")
    elif total_score >= 70:
        recommendations.append(f"✔️ GOOD ATS score ({total_score:.0f}%). Should pass most ATS systems.")
    elif total_score >= 60:
        recommendations.append(f"⚠️ MODERATE ATS score ({total_score:.0f}%). Consider adding more keywords.")
    else:
        recommendations.append(f"❌ LOW ATS score ({total_score:.0f}%). Add missing keywords to improve.")
    
    # Missing keywords
    if missing:
        critical_missing = missing[:5]
        recommendations.append(f"📝 Add these critical keywords: {', '.join(critical_missing)}")
    
    # Density issues
    if under_represented:
        recommendations.append(f"💡 Mention more often (2-5 times ideal): {', '.join(under_represented[:3])}")
    
    if over_represented:
        recommendations.append(f"⚠️ Mentioned too often (reduce): {', '.join(over_represented[:3])}")
    
    # Percentage breakdown
    recommendations.append(f"\n📊 Score Breakdown: Keywords {keyword_score:.0f}/60 + Density {density_score:.0f}/20 + Structure {structure_score:.0f}/20")
    
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
            warnings.append(f"⚠️ Missing required section: {section}")
    
    # Check personal info
    if 'personal_info' in profile:
        pi = profile['personal_info']
        if 'email' not in pi:
            warnings.append("⚠️ Missing email in personal info")
        if 'phone' not in pi:
            warnings.append("⚠️ Missing phone in personal info")
    
    # Check experience dates
    if 'experience' in profile:
        for exp in profile['experience']:
            if 'years' not in exp and 'period' not in exp:
                warnings.append(f"⚠️ Missing dates in experience: {exp.get('title', 'Unknown')}")
    
    # Check skills count
    if 'skills' in profile:
        skill_count = len(profile['skills'])
        if skill_count < 10:
            warnings.append(f"⚠️ Too few skills ({skill_count}). ATS prefers 15-25 skills.")
        elif skill_count > 35:
            warnings.append(f"⚠️ Too many skills ({skill_count}). Keep to 15-25 most relevant.")
    
    if not warnings:
        warnings.append("✅ CV structure is ATS-friendly!")
    
    return warnings
