"""Personal Feng Shui remedies database with classical recommendations."""

from typing import List, Dict
from .knowledge_base import ELEMENT_ATTRIBUTES, BAGUA_AREAS

# Comprehensive remedies database organized by element and purpose
REMEDIES_DB = {
    "wood": [
        {
            "name": "Lucky Bamboo",
            "category": "plants",
            "description": "Brings growth, flexibility, and upward energy",
            "placement": "East or Southeast corner of bedroom or office",
            "cost": "low",
            "difficulty": "easy",
            "benefits": ["career_growth", "health", "family_harmony"],
            "care": "Change water weekly, indirect sunlight"
        },
        {
            "name": "Healthy Green Plants",
            "category": "plants",
            "description": "Living wood energy purifies air and brings vitality",
            "placement": "East area for family, Southeast for wealth",
            "cost": "low",
            "difficulty": "easy",
            "benefits": ["health", "growth", "fresh_energy"],
            "care": "Water regularly, ensure good health"
        },
        {
            "name": "Wooden Furniture",
            "category": "furniture",
            "description": "Natural wood brings grounding wood energy",
            "placement": "Living room, bedroom, office",
            "cost": "medium",
            "difficulty": "medium",
            "benefits": ["stability", "growth", "natural_energy"],
            "care": "Polish regularly, keep clean"
        },
        {
            "name": "Green Color Accents",
            "category": "colors",
            "description": "Green represents wood element and growth",
            "placement": "Walls, cushions, curtains in East/Southeast",
            "cost": "low",
            "difficulty": "easy",
            "benefits": ["growth", "healing", "prosperity"],
            "care": "Keep colors vibrant"
        }
    ],
    "fire": [
        {
            "name": "Himalayan Salt Lamp",
            "category": "lighting",
            "description": "Warm glow brings fire energy and purifies",
            "placement": "South corner, living room, bedroom",
            "cost": "low",
            "difficulty": "easy",
            "benefits": ["recognition", "passion", "energy"],
            "care": "Keep on for several hours daily"
        },
        {
            "name": "Candles (Red/Purple)",
            "category": "lighting",
            "description": "Active fire element for passion and transformation",
            "placement": "South area for fame, Southwest for relationships",
            "cost": "low",
            "difficulty": "easy",
            "benefits": ["passion", "romance", "transformation"],
            "care": "Never leave unattended"
        },
        {
            "name": "Red Decorations",
            "category": "decor",
            "description": "Red is the most auspicious color in feng shui",
            "placement": "South area, entrance, or missing corners",
            "cost": "low",
            "difficulty": "easy",
            "benefits": ["luck", "protection", "vitality"],
            "care": "Keep clean and vibrant"
        },
        {
            "name": "Triangular Art/Decor",
            "category": "decor",
            "description": "Fire-shaped items activate yang energy",
            "placement": "South walls or shelves",
            "cost": "medium",
            "difficulty": "easy",
            "benefits": ["recognition", "success", "energy"],
            "care": "Regular dusting"
        }
    ],
    "earth": [
        {
            "name": "Rose Quartz Crystals",
            "category": "crystals",
            "description": "Earth energy for love and emotional healing",
            "placement": "Southwest corner of bedroom",
            "cost": "low",
            "difficulty": "easy",
            "benefits": ["love", "relationships", "self_care"],
            "care": "Cleanse monthly under moonlight"
        },
        {
            "name": "Citrine Crystal",
            "category": "crystals",
            "description": "Earth stone for abundance and confidence",
            "placement": "Wealth corner (Southeast) or center",
            "cost": "medium",
            "difficulty": "easy",
            "benefits": ["wealth", "confidence", "joy"],
            "care": "Cleanse and recharge in sunlight"
        },
        {
            "name": "Pottery or Ceramics",
            "category": "decor",
            "description": "Handmade earth items bring grounding",
            "placement": "Center of home, Southwest, Northeast",
            "cost": "medium",
            "difficulty": "easy",
            "benefits": ["stability", "grounding", "nourishment"],
            "care": "Keep clean"
        },
        {
            "name": "Yellow/Beige Textiles",
            "category": "colors",
            "description": "Earth colors for stability and warmth",
            "placement": "Center, Southwest, Northeast areas",
            "cost": "low",
            "difficulty": "easy",
            "benefits": ["stability", "relationships", "comfort"],
            "care": "Wash regularly"
        }
    ],
    "metal": [
        {
            "name": "Wind Chimes (Metal)",
            "category": "decor",
            "description": "Moving metal disperses negative energy",
            "placement": "West or Northwest, or in problem areas",
            "cost": "low",
            "difficulty": "easy",
            "benefits": ["clarity", "children", "helpful_people"],
            "care": "Clean occasionally"
        },
        {
            "name": "Metal Singing Bowl",
            "category": "symbols",
            "description": "Sound therapy and metal element",
            "placement": "Meditation space, West area",
            "cost": "medium",
            "difficulty": "medium",
            "benefits": ["clarity", "peace", "focus"],
            "care": "Polish regularly"
        },
        {
            "name": "Round Mirrors",
            "category": "decor",
            "description": "Metal-shaped mirrors expand space and light",
            "placement": "Walls (never facing bed directly)",
            "cost": "low",
            "difficulty": "medium",
            "benefits": ["expansion", "light", "metal_energy"],
            "care": "Keep clean and unbroken"
        },
        {
            "name": "White/Gray Decor",
            "category": "colors",
            "description": "Metal colors bring precision and clarity",
            "placement": "West, Northwest, or children's room",
            "cost": "low",
            "difficulty": "easy",
            "benefits": ["clarity", "organization", "helpful_people"],
            "care": "Keep fresh and clean"
        }
    ],
    "water": [
        {
            "name": "Desktop Fountain",
            "category": "water_features",
            "description": "Flowing water brings wealth and opportunity",
            "placement": "North career area or Southeast wealth area",
            "cost": "medium",
            "difficulty": "medium",
            "benefits": ["career", "wealth", "flow"],
            "care": "Keep water clean, flowing smoothly"
        },
        {
            "name": "Aquarium (if possible)",
            "category": "water_features",
            "description": "Living water with fish attracts abundance",
            "placement": "North, Southeast, or East (never bedroom)",
            "cost": "high",
            "difficulty": "hard",
            "benefits": ["wealth", "career", "vitality"],
            "care": "Regular maintenance essential"
        },
        {
            "name": "Mirrors (Strategic)",
            "category": "decor",
            "description": "Water element - doubles space and energy",
            "placement": "Living room, dining (not bedroom or directly facing door)",
            "cost": "low",
            "difficulty": "medium",
            "benefits": ["expansion", "wealth", "energy"],
            "care": "Keep spotless"
        },
        {
            "name": "Black/Navy Accents",
            "category": "colors",
            "description": "Water colors bring depth and wisdom",
            "placement": "North career area",
            "cost": "low",
            "difficulty": "easy",
            "benefits": ["career", "wisdom", "depth"],
            "care": "Avoid making space too dark"
        }
    ]
}

# Direction-specific remedies
DIRECTION_REMEDIES = {
    "enhance_good_direction": [
        {
            "name": "Place Desk/Bed Facing Lucky Direction",
            "description": "Orient main furniture to face your best direction",
            "cost": "free",
            "difficulty": "medium",
            "benefit": "Maximizes positive energy flow"
        },
        {
            "name": "Enhance with Personal Element",
            "description": "Add your element's colors and objects in this direction",
            "cost": "low",
            "difficulty": "easy",
            "benefit": "Strengthens your personal energy"
        }
    ],
    "remedy_bad_direction": [
        {
            "name": "Avoid Facing While Sleeping/Working",
            "description": "Do not let bed headboard or desk face this direction",
            "cost": "free",
            "difficulty": "medium",
            "benefit": "Prevents energy drain"
        },
        {
            "name": "Place Protective Items",
            "description": "Use mirrors, plants, or crystals to deflect negative energy",
            "cost": "low",
            "difficulty": "easy",
            "benefit": "Neutralizes unfavorable influences"
        }
    ]
}

# Goal-specific remedies
GOAL_REMEDIES = {
    "career": [
        "Desktop fountain in North",
        "Metal desk accessories",
        "Black or dark blue accents",
        "Keep North area clean and uncluttered",
        "Add aquarium if space allows"
    ],
    "wealth": [
        "Lucky bamboo in Southeast",
        "Purple or green decor in Southeast",
        "Citrine crystal in wealth corner",
        "Keep Southeast corner well-lit",
        "Add water feature facing inward"
    ],
    "relationships": [
        "Rose quartz in Southwest bedroom corner",
        "Pairs of items (2 nightstands, 2 candles)",
        "Pink or red accents in Southwest",
        "Remove single-person imagery",
        "Fresh flowers (avoid dried)"
    ],
    "health": [
        "Plants in East family area",
        "Keep center of home clear",
        "Natural light and fresh air",
        "Remove clutter from all areas",
        "Add wood element furniture"
    ],
    "recognition": [
        "Bright lighting in South",
        "Red decorations in South area",
        "Triangular art or frames",
        "Display awards/achievements",
        "Candles in South corner"
    ]
}


def get_remedies_for_element(element: str, max_count: int = 5) -> List[Dict]:
    """Get remedy recommendations for a specific element."""
    return REMEDIES_DB.get(element, [])[:max_count]


def get_remedies_for_goal(goal: str) -> List[str]:
    """Get remedy recommendations for a specific life goal."""
    goal_lower = goal.lower()
    for goal_key in GOAL_REMEDIES.keys():
        if goal_key in goal_lower or goal_lower in goal_key:
            return GOAL_REMEDIES[goal_key]
    return []


def get_budget_friendly_remedies(max_cost: str = "low") -> List[Dict]:
    """Get remedies filtered by budget."""
    cost_hierarchy = {"low": 0, "medium": 1, "high": 2}
    max_level = cost_hierarchy.get(max_cost, 0)
    
    budget_remedies = []
    for element, remedies in REMEDIES_DB.items():
        for remedy in remedies:
            if cost_hierarchy.get(remedy["cost"], 999) <= max_level:
                budget_remedies.append({**remedy, "element": element})
    
    return budget_remedies
