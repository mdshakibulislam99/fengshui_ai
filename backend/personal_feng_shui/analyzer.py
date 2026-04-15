"""Comprehensive Personal Feng Shui AI Analysis Engine.

This module integrates classical Feng Shui formulas (Kua, Ba Zi, Five Elements)
with intelligent recommendations for personalized feng shui guidance.
"""

from datetime import datetime
from typing import Dict, List, Optional
import requests
import logging

from .config import PersonalFengShuiConfig
from .knowledge_base import (
    KUA_DIRECTIONS,
    DIRECTION_MEANINGS,
    LIFE_GOALS_ELEMENTS,
    BAGUA_AREAS,
    ELEMENT_ATTRIBUTES
)
from .bazi_calculator import calculate_bazi_profile
from .element_engine import (
    calculate_element_compatibility,
    balance_elements,
    get_element_enhancements,
    calculate_element_score_for_goal
)
from .remedy_database import (
    get_remedies_for_element,
    get_remedies_for_goal,
    get_budget_friendly_remedies
)

logger = logging.getLogger(__name__)


def _normalize_gender(value: str) -> str:
    """Normalize gender input to standard format."""
    if not isinstance(value, str):
        return "unknown"
    lowered = value.strip().lower()
    if lowered in {"male", "m", "man", "boy"}:
        return "male"
    if lowered in {"female", "f", "woman", "girl"}:
        return "female"
    return "unknown"


def _digital_root(number: int) -> int:
    """Calculate digital root (reduce to single digit)."""
    while number > 9:
        number = sum(int(digit) for digit in str(number))
    return number


def _compute_kua_number(birth_year: int, gender: str) -> int:
    """
    Calculate Kua number using classical Eight Mansions formula.
    
    Formula varies between pre-2000 and post-2000 births.
    Kua 5 is replaced with 2 (female) or 8 (male).
    """
    yy = birth_year % 100
    reduced = _digital_root(yy)

    if birth_year >= 2000:
        if gender == "male":
            kua = 9 - reduced
        elif gender == "female":
            kua = reduced + 6
        else:
            kua = 5
    else:
        if gender == "male":
            kua = 10 - reduced
        elif gender == "female":
            kua = reduced + 5
        else:
            kua = 5

    kua = _digital_root(kua)

    # Replace Kua 5
    if kua == 5:
        return 2 if gender == "female" else 8
    return kua


def _calculate_direction_scores(kua: int, preferred_direction: str) -> Dict:
    """Calculate scores for all directions based on Kua number."""
    kua_data = KUA_DIRECTIONS.get(kua, {})
    
    scores = {}
    for direction_type, meaning_data in DIRECTION_MEANINGS.items():
        direction = kua_data.get(direction_type, "")
        if direction:
            # Good directions get high scores (priority 1-4)
            # Bad directions get low scores (priority 5-8)
            score = 100 - (meaning_data["priority"] - 1) * 12
            scores[direction] = {
                "score": score,
                "type": direction_type,
                "name": meaning_data["name"],
                "benefit": meaning_data["benefit"]
            }
    
    # Check preferred direction
    preferred_upper = str(preferred_direction).strip().upper()
    current_direction_score = 70  # Default
    current_direction_info = None
    
    if preferred_upper:
        for direction, info in scores.items():
            if direction == preferred_upper:
                current_direction_score = info["score"]
                current_direction_info = info
                break
    
    return {
        "all_directions": scores,
        "current_direction_score": current_direction_score,
        "current_direction_info": current_direction_info
    }


def _normalize_priority(value: str) -> str:
    """Collapse mixed priority labels into UI-friendly buckets."""
    normalized = str(value or "medium").strip().lower()
    if "high" in normalized:
        return "high"
    if "low" in normalized:
        return "low"
    return "medium"


def _format_words(value: str) -> str:
    return str(value or "").replace("_", " ").strip().title()


def _direction_quality(score: int) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Supportive"
    if score >= 40:
        return "Mixed"
    return "Challenging"


def _goal_to_bagua_key(goal: str) -> str:
    mapping = {
        "career": "career",
        "wealth": "wealth",
        "relationships": "love",
        "health": "center",
        "family": "family",
        "recognition": "fame"
    }
    return mapping.get(str(goal or "").lower(), "career")


def _build_bagua_guidance() -> Dict:
    alias_map = {
        "career": "career",
        "relationships": "love",
        "family": "family",
        "wealth": "wealth",
        "health": "center",
        "children": "children",
        "knowledge": "knowledge",
        "fame": "fame",
        "helpful_people": "helpful_people"
    }

    guidance = {}
    for public_key, source_key in alias_map.items():
        data = BAGUA_AREAS[source_key]
        direction = _format_words(data["direction"])
        aspect = data["aspect"]
        enhancements = [_format_words(item) for item in data.get("enhancements", [])]
        guidance[public_key] = {
            "direction": direction,
            "element": data["element"],
            "colors": data["colors"],
            "aspect": aspect,
            "guidance": f"Use the {direction} {public_key.replace('_', ' ')} area to support {aspect.lower()}.",
            "enhancements": enhancements,
            "tips": f"Prioritize {', '.join(enhancements[:3])}." if enhancements else ""
        }
    return guidance


def _build_comprehensive_recommendations(
    profile_data: Dict,
    element_analysis: Dict,
    direction_analysis: Dict,
    goals: List[str]
) -> List[Dict]:
    """Generate comprehensive, prioritized recommendations."""
    recommendations = []
    
    kua = profile_data["kua_number"]
    primary_element = profile_data["primary_element"]
    kua_data = KUA_DIRECTIONS.get(kua, {})
    current_direction = str(profile_data.get("preferred_direction", "")).strip().upper()
    current_direction_info = direction_analysis.get("current_direction_info")
    
    # Direction recommendations (HIGH priority)
    best_direction = kua_data.get("sheng_qi", "N")
    health_direction = kua_data.get("tian_yi", "E")
    if current_direction and current_direction_info and current_direction_info["score"] < 60:
        recommendations.append({
            "priority": "high",
            "category": "direction",
            "title": f"Reduce Time Facing {current_direction}",
            "description": f"{current_direction} is currently a {_format_words(current_direction_info['name'])} direction for you, so prolonged work or sleep alignment there can weaken results.",
            "implementation": f"Shift your desk or the head of your bed toward {best_direction}. Use {current_direction} only for low-importance activity if you cannot reorient fully."
        })
    else:
        recommendations.append({
            "priority": "high",
            "category": "direction",
            "title": f"Face {best_direction} for Success",
            "description": f"{best_direction} is your Sheng Qi direction, the strongest orientation for growth, momentum, and visible progress.",
            "implementation": f"Use a compass to orient your main work seat, study area, or bed toward {best_direction} wherever possible."
        })
    
    recommendations.append({
        "priority": "high",
        "category": "direction",
        "title": f"Use {health_direction} as Your Health Direction",
        "description": f"{health_direction} is your Heavenly Doctor direction, which supports recovery, steadier energy, and better daily resilience.",
        "implementation": f"Point your bed, reading chair, or morning routine area toward {health_direction} to reinforce health and stability."
    })
    
    # Element recommendations (MEDIUM priority)
    element_enhancements = get_element_enhancements(primary_element)
    beneficial = element_analysis.get("beneficial_elements", [])
    avoid = element_analysis.get("avoid_elements", [])
    beneficial_text = ", ".join(_format_words(element) for element in beneficial) or _format_words(primary_element)
    avoid_text = ", ".join(_format_words(element) for element in avoid)
    recommendations.append({
        "priority": "medium",
        "category": "element",
        "title": f"Strengthen Your {primary_element.title()} Element",
        "description": f"Your chart is centered on {primary_element} and currently benefits from stronger {beneficial_text.lower()} support to feel more stable and productive.",
        "implementation": f"Use {', '.join(element_enhancements['colors'])} tones and introduce {', '.join(element_enhancements['items'][:3])}.{f' Reduce excess {avoid_text.lower()} accents where possible.' if avoid_text else ''}"
    })
    
    # Goal-specific recommendations (MEDIUM priority)
    for goal in goals[:2]:  # Top 2 goals
        goal_remedies = get_remedies_for_goal(goal)
        bagua_key = _goal_to_bagua_key(goal)
        bagua_data = BAGUA_AREAS[bagua_key]
        goal_direction = _format_words(bagua_data["direction"])
        goal_element = _format_words(bagua_data["element"])
        if goal_remedies:
            recommendations.append({
                "priority": "medium",
                "category": "goal",
                "title": f"Activate {goal.title()} Energy",
                "description": f"Your {goal} goal is best supported through the {goal_direction} area and stronger {goal_element.lower()} element cues.",
                "implementation": f"{'; '.join(goal_remedies[:3])}. Prioritize the {goal_direction} area first."
            })

    return [
        {
            **recommendation,
            "priority": _normalize_priority(recommendation.get("priority"))
        }
        for recommendation in recommendations[:5]
    ]


def analyze_personal_feng_shui(profile: Dict) -> Dict:
    """
    Comprehensive Personal Feng Shui Analysis.
    
    Args:
        profile: Dictionary containing:
            - birthYear (required): int
            - gender (required): str
            - birthMonth (optional): int (1-12)
            - birthDay (optional): int (1-31)
            - goals (optional): list of life goals
            - preferredDirection (optional): current facing direction
            - budget (optional): "low", "medium", "high"
    
    Returns:
        Comprehensive analysis with scores, recommendations, and remedies
    """
    # Validate and extract inputs
    now_year = datetime.now().year
    birth_year = int(profile.get("birthYear", now_year - 30))
    birth_year = max(1900, min(now_year, birth_year))
    
    birth_month = profile.get("birthMonth")
    birth_day = profile.get("birthDay")
    gender = _normalize_gender(profile.get("gender", "unknown"))
    
    goals = profile.get("goals", [])
    if not isinstance(goals, list):
        goals = [str(goals)] if goals else []
    
    preferred_direction = profile.get("preferredDirection", "")
    budget = profile.get("budget", "medium")
    
    # Core calculations
    kua = _compute_kua_number(birth_year, gender)
    kua_info = KUA_DIRECTIONS.get(kua, {})
    
    # Ba Zi analysis (Four Pillars)
    bazi_profile = calculate_bazi_profile(birth_year, birth_month, birth_day)
    
    # Direction analysis
    direction_analysis = _calculate_direction_scores(kua, preferred_direction)
    
    # Element analysis
    primary_element = bazi_profile["day_master"]["element"]
    element_needs = bazi_profile["element_needs"]
    
    # Goal alignment scores
    goal_scores = {}
    for goal in goals:
        goal_elements = LIFE_GOALS_ELEMENTS.get(goal.lower(), {"primary": primary_element})
        goal_scores[goal] = calculate_element_score_for_goal(primary_element, goal_elements)
    
    # Overall score calculation
    weights = PersonalFengShuiConfig.SCORE_WEIGHTS
    element_strength_score = 70 if bazi_profile["day_master"]["strength"] == "moderate" else (85 if bazi_profile["day_master"]["strength"] == "strong" else 55)
    direction_score = direction_analysis["current_direction_score"]
    goal_score = int(sum(goal_scores.values()) / len(goal_scores)) if goal_scores else 70
    
    overall_score = int(
        element_strength_score * weights["element_alignment"] +
        direction_score * weights["direction_alignment"] +
        goal_score * weights["life_goal_match"] +
        75 * weights["element_balance"]  # Placeholder for balance
    )
    
    # Generate classical recommendations (fallback)
    recommendations = _build_comprehensive_recommendations(
        {
            "kua_number": kua,
            "primary_element": primary_element,
            "gender": gender,
            "preferred_direction": preferred_direction
        },
        element_needs,
        direction_analysis,
        goals
    )
    
    # Get specific remedies
    remedies = get_remedies_for_element(primary_element, max_count=3)
    if PersonalFengShuiConfig.ENABLE_ADVANCED_REMEDIES:
        budget_remedies = get_budget_friendly_remedies(budget)[:5]
    else:
        budget_remedies = []
    
    # Compile initial result
    result = {
        "overall_score": overall_score,
        "analysis_level": "detailed" if birth_month else "basic",
        
        "personal_profile": {
            "birth_year": birth_year,
            "age": bazi_profile["age"],
            "gender": gender,
            "kua_number": kua,
            "kua_group": kua_info.get("group", "unknown"),
            "primary_element": primary_element,
            "element_strength": bazi_profile["day_master"]["strength"],
            "life_phase": bazi_profile["life_phase"],
            "life_phase_label": _format_words((bazi_profile["life_phase"] or {}).get("phase", "")),
            "life_phase_description": (bazi_profile["life_phase"] or {}).get("description", "")
        },
        
        "bazi_analysis": {
            "year_pillar": bazi_profile["year_pillar"],
            "day_master": bazi_profile["day_master"],
            "element_needs": element_needs
        },
        
        "directions": {
            "best_direction": kua_info.get("sheng_qi", "N"),
            "health_direction": kua_info.get("tian_yi", "E"),
            "relationship_direction": kua_info.get("nian_yan", "S"),
            "growth_direction": kua_info.get("fu_wei", "N"),
            "worst_direction": kua_info.get("jue_ming", "W"),
            "current_direction": preferred_direction,
            "current_score": direction_score,
            "current_direction_info": direction_analysis.get("current_direction_info"),
            "detailed_scores": direction_analysis["all_directions"],
            "all_directions": [
                {
                    "direction": direction,
                    "score": info["score"],
                    "type": info["type"],
                    "name": info["name"],
                    "benefit": info["benefit"],
                    "quality": _direction_quality(info["score"])
                }
                for direction, info in sorted(direction_analysis["all_directions"].items(), key=lambda item: item[1]["score"], reverse=True)
            ]
        },
        
        "element_balance": {
            "primary_element": primary_element,
            "beneficial_elements": element_needs["beneficial_elements"],
            "avoid_elements": element_needs["avoid_elements"],
            "enhancements": get_element_enhancements(primary_element)
        },
        
        "goal_analysis": {
            "goals": goals,
            "goal_scores": goal_scores,
            "goal_specific_remedies": {goal: get_remedies_for_goal(goal)[:3] for goal in goals[:3]}
        },
        
        "scores": {
            "overall": overall_score,
            "element_alignment": element_strength_score,
            "direction_alignment": direction_score,
            "goal_alignment": goal_score
        },
        
        "recommendations": recommendations[:PersonalFengShuiConfig.MAX_RECOMMENDATIONS],
        
        "remedies": {
            "element_remedies": remedies,
            "budget_friendly": budget_remedies,
            "priority_actions": [r for r in recommendations if r["priority"] == "high"][:3]
        },
        
        "bagua_guidance": _build_bagua_guidance()
    }
    
    # Generate AI-powered personalized recommendations
    classical_recommendations = result["recommendations"][:5]
    ai_recommendations = _generate_ai_recommendations(result, profile)
    result["recommendations"] = ai_recommendations or classical_recommendations
    result["ai_generated"] = bool(ai_recommendations) and ai_recommendations != classical_recommendations
    result["recommendation_source"] = "ai" if result["ai_generated"] else "classical"
    
    return result


def _generate_ai_recommendations(analysis_result: Dict, user_profile: Dict) -> List[Dict]:
    """
    Generate personalized AI recommendations using DeepSeek API.
    Returns structured recommendations or falls back to classical ones if API unavailable.
    """
    try:
        from ..config import Config
        
        # Check if DeepSeek is configured
        api_key = Config.DEEPSEEK_API_KEY
        if not api_key or api_key == 'YOUR_DEEPSEEK_API_KEY_HERE':
            logger.info("DeepSeek API not configured, using classical recommendations")
            return analysis_result.get("recommendations", [])[:5]
        
        # Build context prompt
        profile = analysis_result["personal_profile"]
        directions = analysis_result["directions"]
        goals = user_profile.get("goals", [])
        goals_str = ", ".join(goals) if goals else "general wellness"
        life_phase = profile.get("life_phase")
        if isinstance(life_phase, dict):
            life_phase = f"{life_phase.get('phase', 'unknown')} - {life_phase.get('description', '')}"
        
        prompt = f"""Based on this Feng Shui profile, provide 4-5 specific, actionable recommendations:

Profile: {profile['age']} year old {profile['gender']}, Kua {profile['kua_number']}, Primary Element: {profile['primary_element']}
    Life Phase: {life_phase}
Best Direction: {directions['best_direction']}
Current Goals: {goals_str}
Overall Score: {analysis_result['overall_score']}/100

Provide EXACTLY 4-5 recommendations. For each:
1. Keep it under 40 words
2. Make it specific and actionable
3. Focus on their goals: {goals_str}
4. Include practical implementation steps

Format as JSON array:
[
  {{"priority": "high", "category": "direction", "title": "...", "description": "...", "implementation": "..."}},
  ...
]

Priority levels: high, medium, low
Categories: direction, element, space, lifestyle, habit"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": Config.DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": "You are a Feng Shui master. Provide concise, practical advice in valid JSON format only. No markdown, no explanations outside JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 800,
            "temperature": 0.7
        }
        
        logger.info("Requesting AI recommendations from DeepSeek...")
        response = requests.post(
            Config.DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Try to parse JSON from the response
            import json
            import re
            
            # Extract JSON array if wrapped in markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            elif not content.startswith('['):
                # Try to find JSON array in the content
                json_match = re.search(r'(\[.*?\])', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
            
            recommendations = json.loads(content)
            
            if isinstance(recommendations, list) and len(recommendations) > 0:
                normalized = []
                for recommendation in recommendations[:5]:
                    if not isinstance(recommendation, dict):
                        continue
                    normalized.append({
                        "priority": _normalize_priority(recommendation.get("priority")),
                        "category": str(recommendation.get("category") or "general"),
                        "title": str(recommendation.get("title") or "Personalized Recommendation"),
                        "description": str(recommendation.get("description") or recommendation.get("recommendation") or "").strip(),
                        "implementation": str(recommendation.get("implementation") or "").strip()
                    })
                if normalized:
                    logger.info(f"Successfully generated {len(normalized)} AI recommendations")
                    return normalized
        
        logger.warning(f"DeepSeek API returned status {response.status_code}, using classical recommendations")
        
    except Exception as e:
        logger.error(f"Error generating AI recommendations: {str(e)}")
    
    # Fallback to classical recommendations
    return analysis_result.get("recommendations", [])[:5]
