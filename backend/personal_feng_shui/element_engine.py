"""Five Elements relationship engine for personal feng shui analysis."""

from .knowledge_base import (
    FIVE_ELEMENTS,
    PRODUCTIVE_CYCLE,
    DESTRUCTIVE_CYCLE,
    ELEMENT_ATTRIBUTES
)


def get_supporting_element(element: str) -> str:
    """Get the element that supports/produces this element."""
    for producer, produced in PRODUCTIVE_CYCLE.items():
        if produced == element:
            return producer
    return element


def get_produced_element(element: str) -> str:
    """Get the element produced by this element."""
    return PRODUCTIVE_CYCLE.get(element, element)


def get_controlling_element(element: str) -> str:
    """Get the element that this element controls/weakens."""
    return DESTRUCTIVE_CYCLE.get(element, element)


def get_controlled_by_element(element: str) -> str:
    """Get the element that controls/weakens this element."""
    for controller, controlled in DESTRUCTIVE_CYCLE.items():
        if controlled == element:
            return controller
    return element


def calculate_element_compatibility(element1: str, element2: str) -> dict:
    """Calculate compatibility between two elements."""
    if element1 == element2:
        return {
            "score": 85,
            "relationship": "same",
            "description": f"Both share the {element1} element - harmonious but may lack balance"
        }
    
    # Check productive cycle
    if PRODUCTIVE_CYCLE.get(element1) == element2:
        return {
            "score": 95,
            "relationship": "productive",
            "description": f"{element1.title()} produces {element2.title()} - highly supportive and beneficial"
        }
    
    if PRODUCTIVE_CYCLE.get(element2) == element1:
        return {
            "score": 90,
            "relationship": "nourishing",
            "description": f"{element2.title()} produces {element1.title()} - receiving support and nourishment"
        }
    
    # Check destructive cycle
    if DESTRUCTIVE_CYCLE.get(element1) == element2:
        return {
            "score": 35,
            "relationship": "controlling",
            "description": f"{element1.title()} controls {element2.title()} - potential conflict, needs balancing"
        }
    
    if DESTRUCTIVE_CYCLE.get(element2) == element1:
        return {
            "score": 30,
            "relationship": "weakening",
            "description": f"{element2.title()} controls {element1.title()} - draining energy, needs strengthening"
        }
    
    # Neutral relationship
    return {
        "score": 65,
        "relationship": "neutral",
        "description": f"{element1.title()} and {element2.title()} are neutral - no strong interaction"
    }


def balance_elements(element_scores: dict) -> dict:
    """Analyze element balance and provide recommendations."""
    total = sum(element_scores.values())
    if total == 0:
        return {"balanced": False, "issues": ["No elements present"], "recommendations": []}
    
    # Calculate percentages
    percentages = {elem: (score / total) * 100 for elem, score in element_scores.items()}
    
    # Find deficient and excessive elements
    excessive = [elem for elem, pct in percentages.items() if pct > 30]
    deficient = [elem for elem, pct in percentages.items() if pct < 10]
    
    balanced = len(excessive) == 0 and len(deficient) <= 1
    
    recommendations = []
    
    # Reduce excessive elements
    for elem in excessive:
        controlling = get_controlling_element(elem)
        recommendations.append({
            "action": "reduce",
            "element": elem,
            "method": f"Add more {controlling} element to control excessive {elem}",
            "priority": "high"
        })
    
    # Strengthen deficient elements
    for elem in deficient:
        producing = get_supporting_element(elem)
        recommendations.append({
            "action": "strengthen",
            "element": elem,
            "method": f"Add more {producing} element to support {elem}",
            "priority": "medium"
        })
    
    return {
        "balanced": balanced,
        "percentages": percentages,
        "excessive": excessive,
        "deficient": deficient,
        "recommendations": recommendations
    }


def get_element_enhancements(element: str, context: str = "general") -> list:
    """Get specific items/colors/shapes to enhance an element."""
    attrs = ELEMENT_ATTRIBUTES.get(element, {})
    
    enhancements = {
        "colors": attrs.get("colors", []),
        "shapes": attrs.get("shapes", []),
        "directions": attrs.get("directions", []),
        "items": []
    }
    
    # Element-specific enhancement items
    items_map = {
        "wood": ["plants", "wooden_furniture", "bamboo", "green_textiles", "floral_patterns"],
        "fire": ["candles", "lamps", "red_decorations", "triangular_art", "fireplace"],
        "earth": ["crystals", "ceramics", "pottery", "yellow_cushions", "square_frames"],
        "metal": ["metal_sculptures", "wind_chimes", "white_decor", "round_mirrors", "clocks"],
        "water": ["fountains", "aquarium", "mirrors", "black_accents", "wavy_patterns"]
    }
    
    enhancements["items"] = items_map.get(element, [])
    
    return enhancements


def calculate_element_score_for_goal(primary_element: str, goal_elements: dict) -> int:
    """Calculate how well primary element supports a specific life goal."""
    goal_primary = goal_elements.get("primary", "")
    goal_secondary = goal_elements.get("secondary", "")
    
    score = 50  # Base score
    
    # Direct match
    if primary_element == goal_primary:
        score += 30
    elif primary_element == goal_secondary:
        score += 20
    
    # Productive relationship
    if PRODUCTIVE_CYCLE.get(primary_element) == goal_primary:
        score += 25
    if get_supporting_element(goal_primary) == primary_element:
        score += 20
    
    # Destructive relationship
    if DESTRUCTIVE_CYCLE.get(primary_element) == goal_primary:
        score -= 20
    if get_controlled_by_element(primary_element) == goal_primary:
        score -= 15
    
    return max(0, min(100, score))
