"""
ATS Iterative Refinement System

This module implements an iterative loop that automatically refines CVs
until they achieve 90%+ ATS compatibility score.

Philosophy: Don't give users a bad CV with suggestions - give them a PERFECT CV!
"""

import json
import re
import replicate
from typing import Dict, Any, List, Tuple
from ats_optimizer import predict_ats_score, optimize_profile_for_ats


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
❌ DO NOT change structure (no new experiences/projects/education)
❌ DO NOT remove ANY experiences, projects, or education entries
❌ DO NOT change names, titles, companies, dates
❌ DO NOT create fake information
❌ DO NOT merge or consolidate entries
✅ ONLY enhance descriptions with keywords
✅ ONLY add missing keywords to skills section
✅ ONLY adjust keyword density
✅ MUST preserve ALL entries from input (count: {len(profile.get('experience', []))} experiences, {len(profile.get('projects', []))} projects)

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
    
    print("\n" + "="*70)
    print("🔄 ATS ITERATIVE REFINEMENT - ACHIEVING PERFECTION")
    print("="*70)
    print(f"🎯 Target: {target_score}% ATS Score")
    print(f"🔁 Max Iterations: {max_iterations}")
    print("="*70)
    
    current_profile = profile.copy()
    iteration = 0
    previous_score = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        print(f"\n{'='*70}")
        print(f"📊 ITERATION {iteration}/{max_iterations}")
        print(f"{'='*70}")
        
        # Apply basic ATS optimization (abbreviation expansion)
        if iteration == 1:
            print("\n1️⃣ Applying baseline ATS optimization (abbreviation expansion)...")
            current_profile = optimize_profile_for_ats(current_profile, job_keywords)
        
        # Predict current ATS score
        print(f"\n2️⃣ Calculating ATS score...")
        cv_text = json.dumps(current_profile)
        ats_result = predict_ats_score(cv_text, job_keywords)
        current_score = ats_result['score']
        
        print(f"\n   📊 CURRENT SCORE: {current_score:.1f}%")
        print(f"   📈 Score Breakdown:")
        print(f"      • Keyword Match: {ats_result['keyword_match_score']:.1f}/60")
        print(f"      • Keyword Density: {ats_result['density_score']:.1f}/20")
        print(f"      • Structure: {ats_result['structure_score']:.1f}/20")
        print(f"   ✅ Matched Keywords: {len(ats_result['matched_keywords'])}/{len(job_keywords)}")
        print(f"   ❌ Missing Keywords: {len(ats_result['missing_keywords'])}")
        
        # Check if we've reached target
        if current_score >= target_score:
            print(f"\n🎉 SUCCESS! Achieved {current_score:.1f}% (target: {target_score}%)")
            print(f"✅ Converged in {iteration} iteration(s)")
            return current_profile, ats_result, iteration
        
        # Check if we're making progress
        improvement = current_score - previous_score
        if iteration > 1 and improvement < min_improvement:
            print(f"\n⚠️  Improvement only {improvement:.1f}% (minimum: {min_improvement}%)")
            print(f"   Stopping at {current_score:.1f}% to avoid diminishing returns")
            return current_profile, ats_result, iteration
        
        # Show what needs improvement
        if ats_result['missing_keywords']:
            print(f"\n   🔍 Top Missing Keywords: {', '.join(ats_result['missing_keywords'][:5])}")
        
        if ats_result['under_represented']:
            print(f"   📉 Under-Represented: {', '.join(ats_result['under_represented'][:3])}")
        
        if ats_result['over_represented']:
            print(f"   📈 Over-Represented: {', '.join(ats_result['over_represented'][:3])}")
        
        # Don't refine on last iteration if we haven't reached target
        if iteration == max_iterations:
            print(f"\n⚠️  Reached max iterations ({max_iterations})")
            print(f"   Final score: {current_score:.1f}% (target: {target_score}%)")
            return current_profile, ats_result, iteration
        
        # Refine with LLM
        print(f"\n3️⃣ Refining CV with AI to fix ATS issues...")
        refinement_prompt = create_refinement_prompt(
            current_profile,
            job_keywords,
            ats_result,
            iteration
        )
        
        try:
            refined_json = _call_llm(refinement_prompt, model_name=model_name)
            current_profile = json.loads(refined_json)
            print(f"   ✅ Refinement complete")
        except json.JSONDecodeError as e:
            print(f"   ⚠️  JSON parsing error: {e}")
            print(f"   Keeping previous version and continuing...")
        except Exception as e:
            print(f"   ⚠️  Refinement error: {e}")
            print(f"   Keeping previous version and continuing...")
        
        previous_score = current_score
    
    # Final result
    print(f"\n{'='*70}")
    print(f"🏁 REFINEMENT COMPLETE")
    print(f"{'='*70}")
    print(f"Final Score: {current_score:.1f}% (Target: {target_score}%)")
    print(f"Iterations: {iteration}/{max_iterations}")
    
    return current_profile, ats_result, iteration


def get_ats_summary(ats_result: Dict[str, Any]) -> str:
    """
    Generate a concise summary of ATS performance.
    """
    score = ats_result['score']
    
    if score >= 90:
        status = "🏆 EXCELLENT"
        emoji = "🚀"
    elif score >= 80:
        status = "✅ VERY GOOD"
        emoji = "👍"
    elif score >= 70:
        status = "⚠️  GOOD"
        emoji = "📊"
    else:
        status = "❌ NEEDS IMPROVEMENT"
        emoji = "⚠️"
    
    summary = f"""
{emoji} ATS COMPATIBILITY REPORT {emoji}

Status: {status}
Score: {score:.1f}%

Breakdown:
  • Keyword Match: {ats_result['keyword_match_score']:.1f}/60
  • Keyword Density: {ats_result['density_score']:.1f}/20  
  • Structure: {ats_result['structure_score']:.1f}/20

Keywords: {len(ats_result['matched_keywords'])} matched, {len(ats_result['missing_keywords'])} missing
"""
    
    return summary
