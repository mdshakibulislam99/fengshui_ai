"""Ba Zi (Four Pillars of Destiny) calculator for personal feng shui analysis."""

from datetime import datetime
from typing import Dict, Optional
from .knowledge_base import HEAVENLY_STEMS, EARTHLY_BRANCHES


def calculate_age_from_birth_year(birth_year: int) -> int:
    """Calculate current age."""
    current_year = datetime.now().year
    return current_year - birth_year


def get_heavenly_stem(year: int) -> tuple:
    """Get Heavenly Stem for a given year."""
    stem_index = (year - 4) % 10
    return HEAVENLY_STEMS.get(stem_index, ("unknown", "unknown"))


def get_earthly_branch(year: int) -> tuple:
    """Get Earthly Branch (Chinese Zodiac) for a given year."""
    branch_index = (year - 4) % 12
    return EARTHLY_BRANCHES.get(branch_index, ("unknown", "unknown"))


def calculate_year_pillar(birth_year: int) -> Dict:
    """Calculate the Year Pillar (birth year analysis)."""
    stem_name, stem_element = get_heavenly_stem(birth_year)
    branch_name, branch_element = get_earthly_branch(birth_year)
    
    return {
        "year": birth_year,
        "stem": {"name": stem_name, "element": stem_element},
        "branch": {"name": branch_name, "element": branch_element},
        "pillar_name": f"{stem_name}_{branch_name}",
        "description": f"Year of the {branch_name.title()}"
    }


def get_day_master_strength(day_stem_element: str, month: int, season_elements: dict) -> str:
    """Determine if Day Master is strong or weak based on birth month."""
    # Simplified strength calculation based on season
    season_map = {
        (3, 4, 5): "wood",      # Spring
        (6, 7, 8): "fire",      # Summer
        (9, 10, 11): "metal",   # Autumn
        (12, 1, 2): "water"     # Winter
    }
    
    birth_season = None
    for months, element in season_map.items():
        if month in months:
            birth_season = element
            break
    
    # Strong if Day Master element matches season or is produced by season
    if day_stem_element == birth_season:
        return "strong"
    
    from .element_engine import get_produced_element
    if get_produced_element(birth_season) == day_stem_element:
        return "moderate"
    
    return "weak"


def calculate_life_phase(age: int) -> Dict:
    """Calculate current life phase and energy cycle."""
    phases = [
        (0, 18, "growth", "Learning and foundation building"),
        (18, 35, "expansion", "Career building and relationship formation"),
        (35, 50, "maturity", "Achievement and consolidation"),
        (50, 65, "wisdom", "Leadership and mentorship"),
        (65, 100, "reflection", "Legacy and spiritual focus")
    ]
    
    for start, end, phase_name, description in phases:
        if start <= age < end:
            return {
                "age": age,
                "phase": phase_name,
                "description": description,
                "progress": int(((age - start) / (end - start)) * 100)
            }
    
    return {"age": age, "phase": "eternal", "description": "Living fully", "progress": 100}


def calculate_element_needs(day_master_element: str, day_master_strength: str) -> Dict:
    """Calculate which elements are needed to balance the Day Master."""
    from .element_engine import (
        get_produced_element,
        get_controlling_element,
        get_supporting_element
    )
    
    if day_master_strength == "strong":
        # Need elements to drain or control
        beneficial = [
            get_produced_element(day_master_element),  # Element we produce (drains us)
            get_controlling_element(day_master_element)  # Element we control (drains us)
        ]
        avoid = [get_supporting_element(day_master_element)]  # Makes us too strong
        
    elif day_master_strength == "weak":
        # Need elements to support and strengthen
        beneficial = [
            get_supporting_element(day_master_element),  # Element that produces us
            day_master_element  # Same element (friends)
        ]
        avoid = [get_produced_element(day_master_element)]  # Drains our energy
        
    else:  # moderate
        beneficial = [day_master_element, get_supporting_element(day_master_element)]
        avoid = []
    
    return {
        "beneficial_elements": list(set(beneficial)),
        "avoid_elements": list(set(avoid)),
        "balance_type": day_master_strength
    }


def calculate_bazi_profile(birth_year: int, birth_month: Optional[int] = None, 
                          birth_day: Optional[int] = None) -> Dict:
    """
    Calculate comprehensive Ba Zi profile.
    
    Full Ba Zi requires birth year, month, day, and hour. This simplified version
    focuses on year pillar and provides actionable insights.
    """
    year_pillar = calculate_year_pillar(birth_year)
    age = calculate_age_from_birth_year(birth_year)
    life_phase = calculate_life_phase(age)
    
    # Day Master is simplified to year stem for basic analysis
    day_master_element = year_pillar["stem"]["element"]
    
    # Determine strength (simplified - in full Ba Zi this is much more complex)
    if birth_month:
        day_master_strength = get_day_master_strength(day_master_element, birth_month, {})
    else:
        day_master_strength = "moderate"
    
    element_needs = calculate_element_needs(day_master_element, day_master_strength)
    
    return {
        "year_pillar": year_pillar,
        "day_master": {
            "element": day_master_element,
            "strength": day_master_strength,
            "description": f"Your core energy is {day_master_element} element, currently {day_master_strength}"
        },
        "life_phase": life_phase,
        "element_needs": element_needs,
        "age": age
    }
