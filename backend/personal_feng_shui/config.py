"""Personal Feng Shui module configuration."""

class PersonalFengShuiConfig:
    """Configuration for personal feng shui analysis."""
    
    # Module enable/disable
    ENABLE_BAZI = True  # Four Pillars analysis
    ENABLE_FLYING_STARS = False  # Future feature
    ENABLE_ADVANCED_REMEDIES = True
    
    # Analysis depth levels
    ANALYSIS_LEVEL_BASIC = 1  # Kua number only
    ANALYSIS_LEVEL_DETAILED = 2  # Kua + Elements + Directions
    ANALYSIS_LEVEL_PROFESSIONAL = 3  # Full Ba Zi + Flying Stars
    
    # Scoring weights
    SCORE_WEIGHTS = {
        'element_alignment': 0.35,
        'direction_alignment': 0.30,
        'life_goal_match': 0.20,
        'element_balance': 0.15
    }
    
    # Remedy categories
    REMEDY_CATEGORIES = [
        'crystals',
        'plants',
        'colors',
        'furniture',
        'decor',
        'lighting',
        'water_features',
        'symbols'
    ]
    
    # Recommendation limits
    MAX_RECOMMENDATIONS = 12
    MAX_REMEDIES_PER_CATEGORY = 3
    
    # Timing considerations
    ENABLE_TIMING_ANALYSIS = True
    ENABLE_SEASONAL_ADJUSTMENTS = True
    
    # Report options
    INCLUDE_VISUALIZATIONS = True
    INCLUDE_DETAILED_EXPLANATIONS = True
    INCLUDE_TIMING_GUIDE = True
    INCLUDE_SHOPPING_LIST = False  # Future feature
