"""Classical Feng Shui knowledge base.

Contains all classical formulas, element relationships, Bagua mappings,
and traditional feng shui wisdom organized for AI processing.
"""

# ==================== FIVE ELEMENTS SYSTEM ====================

FIVE_ELEMENTS = ["wood", "fire", "earth", "metal", "water"]

# Productive Cycle: Each element produces/supports the next
PRODUCTIVE_CYCLE = {
    "wood": "fire",      # Wood feeds Fire
    "fire": "earth",     # Fire creates Earth (ash)
    "earth": "metal",    # Earth contains Metal
    "metal": "water",    # Metal collects Water
    "water": "wood"      # Water nourishes Wood
}

# Destructive Cycle: Each element controls/weakens another
DESTRUCTIVE_CYCLE = {
    "wood": "earth",     # Wood depletes Earth
    "earth": "water",    # Earth dams Water
    "water": "fire",     # Water extinguishes Fire
    "fire": "metal",     # Fire melts Metal
    "metal": "wood"      # Metal cuts Wood
}

# Element attributes and characteristics
ELEMENT_ATTRIBUTES = {
    "wood": {
        "colors": ["green", "brown", "teal"],
        "shapes": ["rectangular", "columnar", "vertical"],
        "directions": ["east", "southeast"],
        "season": "spring",
        "qualities": ["growth", "expansion", "flexibility", "creativity"],
        "body_parts": ["liver", "gallbladder", "eyes"],
        "life_areas": ["family", "health", "new_beginnings"]
    },
    "fire": {
        "colors": ["red", "orange", "purple", "pink"],
        "shapes": ["triangular", "pointed", "sharp"],
        "directions": ["south"],
        "season": "summer",
        "qualities": ["passion", "transformation", "recognition", "energy"],
        "body_parts": ["heart", "small_intestine", "tongue"],
        "life_areas": ["fame", "reputation", "social_life"]
    },
    "earth": {
        "colors": ["yellow", "beige", "brown", "tan"],
        "shapes": ["square", "flat", "horizontal"],
        "directions": ["center", "northeast", "southwest"],
        "season": "late_summer",
        "qualities": ["stability", "nourishment", "grounding", "reliability"],
        "body_parts": ["stomach", "spleen", "pancreas"],
        "life_areas": ["relationships", "self_care", "knowledge"]
    },
    "metal": {
        "colors": ["white", "gray", "silver", "gold"],
        "shapes": ["circular", "oval", "spherical"],
        "directions": ["west", "northwest"],
        "season": "autumn",
        "qualities": ["precision", "efficiency", "clarity", "organization"],
        "body_parts": ["lungs", "large_intestine", "skin"],
        "life_areas": ["children", "creativity", "helpful_people"]
    },
    "water": {
        "colors": ["black", "dark_blue", "navy"],
        "shapes": ["wavy", "flowing", "irregular"],
        "directions": ["north"],
        "season": "winter",
        "qualities": ["wisdom", "flow", "communication", "introspection"],
        "body_parts": ["kidneys", "bladder", "ears"],
        "life_areas": ["career", "life_path", "wisdom"]
    }
}

# ==================== BAGUA MAP (9 LIFE AREAS) ====================

BAGUA_AREAS = {
    "wealth": {
        "direction": "southeast",
        "element": "wood",
        "colors": ["purple", "green", "gold"],
        "aspect": "Prosperity, abundance, financial success",
        "enhancements": ["water_features", "plants", "purple_items"]
    },
    "fame": {
        "direction": "south",
        "element": "fire",
        "colors": ["red", "orange"],
        "aspect": "Recognition, reputation, social status",
        "enhancements": ["lights", "candles", "red_items", "awards"]
    },
    "love": {
        "direction": "southwest",
        "element": "earth",
        "colors": ["pink", "red", "white"],
        "aspect": "Romance, marriage, partnerships",
        "enhancements": ["pairs_of_items", "rose_quartz", "pink_decor"]
    },
    "family": {
        "direction": "east",
        "element": "wood",
        "colors": ["green", "brown"],
        "aspect": "Family, health, community",
        "enhancements": ["family_photos", "plants", "wooden_items"]
    },
    "center": {
        "direction": "center",
        "element": "earth",
        "colors": ["yellow", "earth_tones"],
        "aspect": "Balance, harmony, grounding",
        "enhancements": ["open_space", "yellow_items", "crystals"]
    },
    "children": {
        "direction": "west",
        "element": "metal",
        "colors": ["white", "metallic"],
        "aspect": "Children, creativity, projects",
        "enhancements": ["metal_items", "white_decor", "creative_art"]
    },
    "knowledge": {
        "direction": "northeast",
        "element": "earth",
        "colors": ["blue", "green", "black"],
        "aspect": "Wisdom, self-cultivation, spirituality",
        "enhancements": ["books", "meditation_items", "quiet_space"]
    },
    "career": {
        "direction": "north",
        "element": "water",
        "colors": ["black", "dark_blue"],
        "aspect": "Career, life path, opportunities",
        "enhancements": ["water_features", "mirrors", "black_items"]
    },
    "helpful_people": {
        "direction": "northwest",
        "element": "metal",
        "colors": ["gray", "white", "silver"],
        "aspect": "Mentors, travel, synchronicity",
        "enhancements": ["metal_items", "gray_decor", "travel_photos"]
    }
}

# ==================== KUA NUMBERS & DIRECTIONS ====================

# East Group (Kua 1, 3, 4, 9) vs West Group (Kua 2, 6, 7, 8)
EAST_GROUP = [1, 3, 4, 9]
WEST_GROUP = [2, 6, 7, 8]

# Lucky and unlucky directions for each Kua number
KUA_DIRECTIONS = {
    1: {
        "group": "east",
        "element": "water",
        "sheng_qi": "SE",      # Best - Success
        "tian_yi": "E",        # Health
        "nian_yan": "S",       # Relationships
        "fu_wei": "N",         # Personal growth
        "huo_hai": "W",        # Bad luck
        "wu_gui": "NE",        # Five ghosts
        "lui_sha": "SW",       # Six killings
        "jue_ming": "NW"       # Total loss
    },
    2: {
        "group": "west",
        "element": "earth",
        "sheng_qi": "NE",
        "tian_yi": "W",
        "nian_yan": "NW",
        "fu_wei": "SW",
        "huo_hai": "E",
        "wu_gui": "SE",
        "lui_sha": "S",
        "jue_ming": "N"
    },
    3: {
        "group": "east",
        "element": "wood",
        "sheng_qi": "S",
        "tian_yi": "N",
        "nian_yan": "SE",
        "fu_wei": "E",
        "huo_hai": "SW",
        "wu_gui": "NW",
        "lui_sha": "NE",
        "jue_ming": "W"
    },
    4: {
        "group": "east",
        "element": "wood",
        "sheng_qi": "N",
        "tian_yi": "S",
        "nian_yan": "E",
        "fu_wei": "SE",
        "huo_hai": "NW",
        "wu_gui": "SW",
        "lui_sha": "W",
        "jue_ming": "NE"
    },
    6: {
        "group": "west",
        "element": "metal",
        "sheng_qi": "W",
        "tian_yi": "NE",
        "nian_yan": "SW",
        "fu_wei": "NW",
        "huo_hai": "SE",
        "wu_gui": "E",
        "lui_sha": "N",
        "jue_ming": "S"
    },
    7: {
        "group": "west",
        "element": "metal",
        "sheng_qi": "NW",
        "tian_yi": "SW",
        "nian_yan": "NE",
        "fu_wei": "W",
        "huo_hai": "N",
        "wu_gui": "S",
        "lui_sha": "SE",
        "jue_ming": "E"
    },
    8: {
        "group": "west",
        "element": "earth",
        "sheng_qi": "SW",
        "tian_yi": "NW",
        "nian_yan": "W",
        "fu_wei": "NE",
        "huo_hai": "S",
        "wu_gui": "N",
        "lui_sha": "E",
        "jue_ming": "SE"
    },
    9: {
        "group": "east",
        "element": "fire",
        "sheng_qi": "E",
        "tian_yi": "SE",
        "nian_yan": "N",
        "fu_wei": "S",
        "huo_hai": "NE",
        "wu_gui": "W",
        "lui_sha": "NW",
        "jue_ming": "SW"
    }
}

# Direction meanings
DIRECTION_MEANINGS = {
    "sheng_qi": {"name": "Generating Breath", "benefit": "Success & prosperity", "priority": 1},
    "tian_yi": {"name": "Heavenly Doctor", "benefit": "Health & healing", "priority": 2},
    "nian_yan": {"name": "Longevity", "benefit": "Relationships & romance", "priority": 3},
    "fu_wei": {"name": "Personal Growth", "benefit": "Stability & self-development", "priority": 4},
    "huo_hai": {"name": "Accidents", "benefit": "Avoid - minor mishaps", "priority": 5},
    "wu_gui": {"name": "Five Ghosts", "benefit": "Avoid - conflicts & obstacles", "priority": 6},
    "lui_sha": {"name": "Six Killings", "benefit": "Avoid - health & legal issues", "priority": 7},
    "jue_ming": {"name": "Total Loss", "benefit": "AVOID - worst direction", "priority": 8}
}

# ==================== ELEMENT YEAR CYCLE ====================

# Heavenly Stems cycle (10-year cycle)
HEAVENLY_STEMS = {
    0: ("yang_metal", "metal"),
    1: ("yin_metal", "metal"),
    2: ("yang_water", "water"),
    3: ("yin_water", "water"),
    4: ("yang_wood", "wood"),
    5: ("yin_wood", "wood"),
    6: ("yang_fire", "fire"),
    7: ("yin_fire", "fire"),
    8: ("yang_earth", "earth"),
    9: ("yin_earth", "earth")
}

# Earthly Branches cycle (12-year cycle - Chinese Zodiac)
EARTHLY_BRANCHES = {
    0: ("rat", "water"),
    1: ("ox", "earth"),
    2: ("tiger", "wood"),
    3: ("rabbit", "wood"),
    4: ("dragon", "earth"),
    5: ("snake", "fire"),
    6: ("horse", "fire"),
    7: ("goat", "earth"),
    8: ("monkey", "metal"),
    9: ("rooster", "metal"),
    10: ("dog", "earth"),
    11: ("pig", "water")
}

# ==================== LIFE GOALS MAPPING ====================

LIFE_GOALS_ELEMENTS = {
    "career": {"primary": "water", "secondary": "metal"},
    "wealth": {"primary": "wood", "secondary": "water"},
    "health": {"primary": "earth", "secondary": "metal"},
    "relationships": {"primary": "earth", "secondary": "fire"},
    "family": {"primary": "wood", "secondary": "earth"},
    "recognition": {"primary": "fire", "secondary": "wood"},
    "knowledge": {"primary": "earth", "secondary": "water"},
    "creativity": {"primary": "metal", "secondary": "fire"},
    "travel": {"primary": "metal", "secondary": "water"},
    "spirituality": {"primary": "earth", "secondary": "metal"}
}
