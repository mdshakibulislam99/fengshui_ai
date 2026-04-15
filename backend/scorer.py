# Module for calculating final weighted Feng Shui scores and generating suggestions

import logging
from typing import Dict, List, Optional, Tuple
import math
from datetime import datetime
import time

from .config import config
from .ai_model import predict_feng_shui_score

logger = logging.getLogger(__name__)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _rural_context_factor(features: Dict) -> float:
    """
    Estimate whether a location behaves like a sparse/rural context.
    1.0 = strongly rural/sparse, 0.0 = dense urban context.
    """
    density = _clamp01(features.get('building_density', 0.0))
    road = _clamp01(features.get('road_intersection_density', 0.0))
    # Buildings dominate the context signal, roads provide secondary evidence.
    urban_intensity = _clamp01(density * 0.65 + road * 0.35)
    return 1.0 - urban_intensity


def _data_signal_strength(features: Dict) -> float:
    """
    Estimate direct local signal coverage from map-derived features.
    Higher values mean AI model output can be trusted more.
    """
    signals = [
        min(_clamp01(features.get('green_area_ratio', 0.0)) * 5.0, 1.0),
        _clamp01(features.get('water_proximity', 0.0)),
        _clamp01(features.get('environmental_quality', 0.0)),
        _clamp01(features.get('spiritual_presence', 0.0)),
        min(_clamp01(features.get('road_intersection_density', 0.0)) * 2.0, 1.0),
        min(_clamp01(features.get('total_buildings_nearby', 0.0)) * 2.0, 1.0),
    ]
    return sum(signals) / len(signals)


def _infer_reputation_tier(location_context: Optional[Dict]) -> Dict[str, Optional[str]]:
    """
    Infer known Feng Shui reputation tier from location label/address.
    
    TIER 3: Enhanced reputation database with more legendary Feng Shui sites.
    """
    if not isinstance(location_context, dict):
        return {'tier': None, 'matched_keyword': None}

    lat = location_context.get('latitude')
    lng = location_context.get('longitude')
    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (TypeError, ValueError):
        lat_f = None
        lng_f = None

    address = str(location_context.get('address', '') or '').strip().lower()
    if not address:
        # Coordinate fallback for known landmarks when address text is missing or garbled.
        if lat_f is not None and lng_f is not None:
            if abs(lat_f - 29.921911) <= 0.02 and abs(lng_f - 118.286296) <= 0.02:
                return {'tier': 'legendary', 'matched_keyword': 'chengkan-coords'}
        return {'tier': None, 'matched_keyword': None}

    # TIER 3: Enhanced legendary site database
    legendary_sites = {
        'chengkan': [
            '呈坎', '呈坎古村', 'chengkan',
            '罗贤能宅', '宇宙之村',
        ],
        'yangzhou': [
            '扬州', 'yangzhou', '瘦西湖',
        ],
        'suzhou': [
            '苏州', 'suzhou', '拙政园', '留园',
        ],
        'guilin': [
            '桂林', 'guilin', '漓江', '阳朔',
        ],
        'hangzhou': [
            '杭州', 'hangzhou', '西湖',
        ],
        'nanjing': [
            '南京', 'nanjing', '中山陵', '秦淮河',
        ],
    }
    
    strong_sites = {
        'langzhong': [
            '阆中', 'langzhong', '风水古城',
        ],
        'wudang': [
            '武当山', 'wudang', '太极',
        ],
        'shaolin': [
            '少林', 'shaolin', '登封', '嵩山',
        ],
        'longmen': [
            '龙门', 'longmen', '洛阳', '伊河',
        ],
        'beijing': [
            '北京', 'beijing', '故宫', '紫禁城', '昆明湖',
        ],
        'xian': [
            '西安', 'xian', '大雁塔', '城墙',
        ],
    }
    
    # Check legendary sites
    for site_key, keywords in legendary_sites.items():
        for keyword in keywords:
            if keyword.lower() in address:
                return {'tier': 'legendary', 'matched_keyword': keyword}

    # Check strong sites
    for site_key, keywords in strong_sites.items():
        for keyword in keywords:
            if keyword.lower() in address:
                return {'tier': 'strong', 'matched_keyword': keyword}

    # Coordinate fallback for known landmarks when textual matching fails.
    if lat_f is not None and lng_f is not None:
        if abs(lat_f - 29.921911) <= 0.02 and abs(lng_f - 118.286296) <= 0.02:
            return {'tier': 'legendary', 'matched_keyword': 'chengkan-coords'}
        # Chengkan coordinates
        if abs(lat_f - 29.8) <= 0.01 and abs(lng_f - 118.3) <= 0.01:
            return {'tier': 'legendary', 'matched_keyword': 'anhui-historical'}

    return {'tier': None, 'matched_keyword': None}


# ============================================================================
# TIER 1: ENHANCED WATER ANALYSIS (朝阳水 - Auspicious Water Orientation)
# ============================================================================

def _get_water_direction_score(latitude: float, longitude: float, aspects_degrees: Optional[float] = None) -> float:
    """
    Calculate auspicious water orientation score (朝阳水).
    
    Feng Shui principle: Water should face south/southeast (朝阳 = facing sun)
    for maximum wealth and prosperity benefits.
    
    Args:
        latitude: Location latitude (used for hemisphere adjustment)
        longitude: Location longitude  
        aspects_degrees: Dominant aspect angle from topography (0-360 degrees)
    
    Returns:
        Score 0-1 (higher = more auspicious water orientation)
    """
    # Northern hemisphere: target South (180°) / Southeast (135°)
    # Southern hemisphere: target North (0°) / Northeast (45°)
    is_northern = latitude >= 0
    
    if aspects_degrees is None:
        return 0.5  # Neutral, no aspect data
    
    target_angle = 180 if is_northern else 0  # South (N) or North (S)
    
    # Calculate angular distance from optimal (minimize diff from target ±45°)
    angle_diff = abs(aspects_degrees - target_angle)
    if angle_diff > 180:
        angle_diff = 360 - angle_diff
    
    # Score: 1.0 at target ±20°, drops to 0 at ±90°
    if angle_diff <= 20:
        return 1.0
    elif angle_diff <= 90:
        return max(0.0, 1.0 - (angle_diff - 20) / 70.0)
    else:
        return 0.2  # Always some benefit from water presence


def _calculate_water_quality_proxy(hydrosheds_density: float, flood_risk: float) -> float:
    """
    Estimate water quality proxy (cleanliness/purity) from hydrological metrics.
    
    Pure flowing water (high hydrosheds density, low flood risk) = better quality.
    Stagnant/flooded areas = poor quality.
    
    Returns:
        Score 0-1 (higher = better water quality)
    """
    # Flowing water indicator: high river density + moderate flow
    flow_quality = max(0.0, hydrosheds_density * 0.6 - flood_risk * 0.4)
    
    # Avoid pure stagnation (flood risk 0.8+ indicates problematic water)
    quality_penalty = 0.0 if flood_risk < 0.6 else (flood_risk - 0.6) * 0.5
    
    return max(0.0, min(1.0, flow_quality - quality_penalty))


def _detect_mountain_water_relationship(green_score: float, water_score: float, 
                                        topo_score: float, building_density: float) -> Tuple[float, str]:
    """
    Detect traditional 背山面水 (backed by mountains, facing water) configuration.
    
    This is one of the most important Feng Shui principles. Returns confidence
    and description of configuration detected.
    
    Returns:
        (configuration_score: 0-1, description: str)
    """
    # Background mountains: high topography + low buildings = natural backdrop
    mountains_present = topo_score > 0.5 and building_density < 0.6
    
    # Facing water: good water access + open space facing it
    water_present = water_score > 0.4
    
    # Open foreground: low building density to "face" the water
    open_foreground = building_density < 0.4
    
    # Enclosed background: mountains/high terrain to support from behind
    enclosed_back = topo_score > 0.5
    
    if mountains_present and water_present and open_foreground:
        confidence = min(1.0, topo_score * 0.6 + water_score * 0.25 + (1.0 - building_density) * 0.15)
        description = "Ideal 背山面水 (mountain-backed, water-facing) configuration detected"
        return (confidence, description)
    elif water_present and open_foreground:
        confidence = water_score * 0.7 + (1.0 - building_density) * 0.3
        description = "Water-facing configuration with open foreground"
        return (confidence, description)
    elif mountains_present:
        confidence = topo_score * 0.6 + (1.0 - building_density) * 0.4
        description = "Mountain-backed configuration detected"
        return (confidence, description)
    else:
        return (0.0, "Classical mountain-water configuration not detected")


# ============================================================================
# TIER 1: ENHANCED ENVIRONMENTAL QUALITY (Air, Noise, Light)
# ============================================================================

def _estimate_air_quality_from_features(environmental_quality: float, green_area: float, 
                                       building_density: float) -> float:
    """
    Estimate air quality proxy using available environmental indicators.
    
    Good proxy factors: high green space, low density (better dispersion),
    good environmental quality score (hospitals/schools proximity).
    
    Returns:
        Score 0-1 (higher = better air quality, lower = more pollution risk)
    """
    # Green areas act as natural air filters
    green_factor = green_area * 0.4
    
    # Dense buildings trap pollution
    density_penalty = building_density * 0.3
    
    # General environmental quality (proximity to services indicates developed infrastructure)
    env_factor = environmental_quality * 0.3
    
    air_score = green_factor + env_factor - density_penalty
    return max(0.0, min(1.0, air_score))


def _estimate_noise_level_from_features(road_density: float, building_density: float) -> float:
    """
    Estimate noise level proxy from road and building density.
    
    High road density + high building density = sound amplification (worse).
    Low road density + low buildings = quieter.
    
    Returns:
        Score 0-1 (higher = greater noise pollution problem)
    """
    # Road density is primary noise source
    road_noise = road_density * 0.6
    
    # Dense buildings amplify and trap sound
    building_amplification = building_density * 0.4
    
    noise_problem = road_noise + building_amplification
    return max(0.0, min(1.0, noise_problem))


def _estimate_sunlight_exposure(aspect_degrees: Optional[float], latitude: float, 
                               building_density: float) -> float:
    """
    Estimate sunlight exposure quality based on aspect and location.
    
    Optimal: South-facing in Northern Hemisphere (180°), North-facing in Southern.
    Penalize for high building density which blocks sunlight.
    
    Returns:
        Score 0-1 (higher = better sunlight exposure)
    """
    if aspect_degrees is None:
        base_sun = 0.5
    else:
        # In northern hemisphere: 180° (south) is optimal, 90° (east) and 270° (west) are okay
        is_northern = latitude >= 0
        target = 180 if is_northern else 0
        
        angle_diff = abs(aspect_degrees - target)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        # Full sun at optimal, decreases with angle difference
        base_sun = max(0.3, 1.0 - angle_diff / 270.0)
    
    # Building density reduces effective sunlight
    building_obstruction = building_density * 0.3
    
    sunlight_score = base_sun - building_obstruction
    return max(0.0, min(1.0, sunlight_score))


# ============================================================================
# TIER 2: FEATURE INTERACTION DETECTION (Synergies & Correlations)
# ============================================================================

def _calculate_feature_interactions(features: Dict) -> Dict[str, float]:
    """
    Detect and score feature interactions (synergistic effects).
    
    Examples:
    - Green + Water synergy (water-nourished gardens)
    - Good orientation + open space (better chi flow)
    - Mountain backdrop + water facing (classical config)
    - Low noise + high air quality (healthy environment)
    
    Returns:
        Dict of interaction scores
    """
    interactions = {}
    
    # Synergy 1: Green-Water Harmony (water sustains plants)
    green = _clamp01(features.get('green_area_ratio', 0.0))
    water = _clamp01(features.get('water_proximity', 0.0))
    river = _clamp01(features.get('hydrosheds_river_proximity', 0.5))
    
    green_water_synergy = (green * water * 1.5) + (green * river * 0.8)
    interactions['green_water_harmony'] = min(1.0, green_water_synergy)
    
    # Synergy 2: Qi Flow Optimization (orientation + openness)
    orientation = _clamp01(features.get('orientation_score', 0.5))
    density = _clamp01(features.get('building_density', 0.0))
    qi_flow = _clamp01(features.get('qi_flow', 0.5))
    
    qi_opt_synergy = (orientation * (1.0 - density) * qi_flow) * 1.3
    interactions['qi_flow_optimization'] = min(1.0, qi_opt_synergy)
    
    # Synergy 3: Environmental Harmony (clean air + low noise + good quality)
    env_quality = _clamp01(features.get('environmental_quality', 0.0))
    topography = _clamp01(features.get('topography_score', 0.5))
    
    air_quality = _estimate_air_quality_from_features(env_quality, green, density)
    noise_problem = _estimate_noise_level_from_features(
        _clamp01(features.get('road_intersection_density', 0.0)), density
    )
    
    env_harmony = (env_quality * air_quality * (1.0 - noise_problem)) * 1.2
    interactions['environmental_harmony'] = min(1.0, env_harmony)
    
    # Synergy 4: Mountain-Water Configuration (classical Feng Shui)
    # Calculated separately but cached here
    green_score_est = green * 100.0
    water_score_est = water * 100.0
    config_score, _ = _detect_mountain_water_relationship(
        green_score_est, water_score_est, topography, density
    )
    interactions['mountain_water_config'] = config_score
    
    # Synergy 5: Spiritual-Natural Harmony (temples/sites + nature)
    spiritual = _clamp01(features.get('spiritual_presence', 0.0))
    natural_harmony = (spiritual * topography * green) * 1.3
    interactions['spiritual_natural_harmony'] = min(1.0, natural_harmony)
    
    return interactions


# ============================================================================
# TIER 2+3: SEASONAL & TEMPORAL ADJUSTMENTS
# ============================================================================

def _get_seasonal_adjustment_factor(latitude: float, month: Optional[int] = None) -> Dict[str, float]:
    """
    Apply seasonal adjustments to Feng Shui scoring.
    
    Different seasons favor different elements (Wood=Spring, Fire=Summer, etc).
    
    Returns:
        Dict with seasonal modifiers for each category
    """
    if month is None:
        month = datetime.now().month
    
    # Determine season
    if month in [3, 4, 5]:
        season = 'spring'
        element = 'wood'
    elif month in [6, 7, 8]:
        season = 'summer'
        element = 'fire'
    elif month in [9, 10, 11]:
        season = 'autumn'
        element = 'metal'
    else:
        season = 'winter'
        element = 'water'
    
    # Latitude-based seasonal emphasis (tropical vs temperate)
    is_tropical = abs(latitude) < 23.5
    
    if season == 'spring':
        modifiers = {
            'green_space': 1.15 if not is_tropical else 1.05,  # Spring green growth
            'water_element': 1.0,
            'orientation': 1.10,  # Fresh east-facing energy
            'environmental': 1.05,
        }
    elif season == 'summer':
        modifiers = {
            'green_space': 1.05,
            'water_element': 1.15 if not is_tropical else 1.05,  # More water needed in heat
            'orientation': 1.0,
            'environmental': 1.05,
        }
    elif season == 'autumn':
        modifiers = {
            'green_space': 0.95,  # Foliage loss
            'water_element': 1.05,  # Metal season increases water value
            'orientation': 1.05,  # Crisp air enhances orientation
            'environmental': 1.10,
        }
    else:  # winter
        modifiers = {
            'green_space': 0.90,  # Minimal vegetation
            'water_element': 1.20,  # Water element dominant
            'orientation': 1.0,
            'environmental': 0.95,  # Harsher conditions
        }
    
    return {
        'season': season,
        'element': element,
        'is_tropical': is_tropical,
        'modifiers': modifiers
    }


# ============================================================================
# TIER 3: EXPERT VALIDATION FRAMEWORK
# ============================================================================

def _init_expert_validation_tracker() -> Dict:
    """
    Initialize structure for tracking expert assessments and feedback.
    
    This enables learning from expert Feng Shui practitioners' evaluations.
    """
    return {
        'assessments': [],  # List of expert evaluations
        'expert_confidence': {},  # Per-location expert confidence
        'model_divergences': {},  # Cases where model differs from expert
        'learning_signal': 0.0,  # Aggregate learning score (0-1)
        'validation_date': datetime.now().isoformat(),
    }


def _record_expert_assessment(expert_id: str, location_hash: str, expert_score: float,
                             ai_score: float, feedback: str) -> Dict:
    """
    Record an expert Feng Shui assessment for model validation/training.
    
    Args:
        expert_id: Unique identifier of expert practitioner
        location_hash: Hash of (lat, lng) for tracking
        expert_score: Expert assessment (0-100)
        ai_score: System's AI score (0-100)
        feedback: Expert commentary on scoring
    
    Returns:
        Assessment record with analysis
    """
    divergence = abs(expert_score - ai_score)
    is_significant_divergence = divergence > 15
    
    assessment = {
        'expert_id': expert_id,
        'location_hash': location_hash,
        'expert_score': expert_score,
        'ai_score': ai_score,
        'divergence': divergence,
        'is_significant': is_significant_divergence,
        'feedback': feedback,
        'timestamp': datetime.now().isoformat(),
    }
    
    if is_significant_divergence:
        logger.warning(
            f"Significant divergence detected: Expert={expert_score:.0f}, "
            f"AI={ai_score:.0f}, Diff={divergence:.1f}, Expert: {expert_id}"
        )
    
    return assessment





def calculate_feng_shui_score(features: Dict, location_context: Optional[Dict] = None) -> Dict:
    """
    Calculate final Feng Shui score based on extracted features.
    Combines traditional Feng Shui principles with AI predictions.
    
    Args:
        features: Dictionary of extracted features
    
    Returns:
        Dictionary with:
        {
            'final_score': float (0-100),
            'category_scores': dict,
            'explanations': list,
            'suggestions': list,
            'yin_yang_balance': float,
            'five_elements': dict,
            'qi_flow_score': float
        }
    """
    logger.info("Calculating comprehensive Feng Shui score...")
    score_start_ts = time.monotonic()
    
    # Calculate individual category scores (0-100 scale)
    category_scores = {
        'green_space': calculate_green_space_score(features),
        'water_element': calculate_water_score(features),
        'building_harmony': calculate_building_score(features),
        'road_accessibility': calculate_road_score(features),
        'orientation': calculate_orientation_category_score(features),
        'environment': calculate_environment_score(features),
        'spiritual_energy': calculate_spiritual_score(features)
    }
    
    # Calculate Yin-Yang balance
    yin_yang_balance = calculate_yin_yang_balance(features, category_scores)
    category_scores['yin_yang_balance'] = yin_yang_balance
    
    # Calculate Five Elements harmony
    five_elements = calculate_five_elements(features, category_scores)
    category_scores['five_elements_harmony'] = five_elements['overall_score']
    
    # Calculate Qi flow score
    qi_flow_score = calculate_qi_flow(features, category_scores)
    category_scores['qi_flow'] = qi_flow_score
    
    # Calculate traditional weighted score
    weights = config.FEATURE_WEIGHTS
    traditional_score = (
        category_scores['green_space'] * weights['green_area_ratio'] +
        category_scores['water_element'] * weights['water_proximity'] +
        category_scores['building_harmony'] * weights['building_density'] +
        category_scores['road_accessibility'] * weights['road_density'] +
        category_scores['orientation'] * weights['orientation'] +
        category_scores['environment'] * weights['environmental'] +
        category_scores['spiritual_energy'] * weights['spiritual']
    )
    
    # TIER 2: Apply feature interaction synergies (BONUS BOOST)
    interactions = _calculate_feature_interactions(features)
    interaction_boost = (
        interactions['green_water_harmony'] * 0.05 +
        interactions['qi_flow_optimization'] * 0.05 +
        interactions['environmental_harmony'] * 0.04 +
        interactions['mountain_water_config'] * 0.03 +
        interactions['spiritual_natural_harmony'] * 0.03
    )
    traditional_score = traditional_score + interaction_boost
    
    logger.info(
        f"✓ Feature interactions detected: "
        f"green_water={interactions['green_water_harmony']:.2f}, "
        f"qi_flow={interactions['qi_flow_optimization']:.2f}, "
        f"env_harmony={interactions['environmental_harmony']:.2f}, "
        f"mountain_water={interactions['mountain_water_config']:.2f}, "
        f"spiritual={interactions['spiritual_natural_harmony']:.2f}; "
        f"Total bonus: +{interaction_boost:.2f} points"
    )
    
    # TIER 3: Apply seasonal adjustments
    latitude = features.get('latitude', 30.0)
    seasonal_info = _get_seasonal_adjustment_factor(latitude)
    modifiers = seasonal_info['modifiers']
    
    logger.info(
        f"✓ Seasonal adjustment applied: {seasonal_info['season'].upper()} "
        f"(Element: {seasonal_info['element']}, Tropical: {seasonal_info['is_tropical']})"
    )
    
    # Apply seasonal modifiers to relevant categories
    temp_green = category_scores['green_space'] * modifiers.get('green_space', 1.0)
    temp_water = category_scores['water_element'] * modifiers.get('water_element', 1.0)
    temp_oritn = category_scores['orientation'] * modifiers.get('orientation', 1.0)
    temp_env = category_scores['environment'] * modifiers.get('environmental', 1.0)
    
    logger.info(
        f"  Seasonal modifiers: green×{modifiers.get('green_space', 1.0):.2f}, "
        f"water×{modifiers.get('water_element', 1.0):.2f}, "
        f"orient×{modifiers.get('orientation', 1.0):.2f}, "
        f"env×{modifiers.get('environmental', 1.0):.2f}"
    )
    
    # Recalculate traditional score with seasonal adjustments
    traditional_score_seasonal = (
        temp_green * weights['green_area_ratio'] +
        temp_water * weights['water_proximity'] +
        category_scores['building_harmony'] * weights['building_density'] +
        category_scores['road_accessibility'] * weights['road_density'] +
        temp_oritn * weights['orientation'] +
        temp_env * weights['environmental'] +
        category_scores['spiritual_energy'] * weights['spiritual']
    )
    
    # Blend seasonal adjustment (40% weight)
    traditional_score = traditional_score * 0.6 + traditional_score_seasonal * 0.4
    
    logger.info(
        f"✓ Score composition: "
        f"base={traditional_score - interaction_boost:.2f}, "
        f"interactions=+{interaction_boost:.2f}, "
        f"seasonal adjustment applied (40% weight)"
    )
    
    # Cap at 100
    traditional_score = min(100.0, traditional_score)
    
    # Get AI prediction
    ai_result = predict_feng_shui_score(features)
    
    # Combine traditional and AI scores (70% traditional, 30% AI)
    if ai_result:
        ai_score = ai_result['ai_score']
        
        # CAMPUS LOCATION DETECTION AND CORRECTION
        # AI model trained on urban commercial features; doesn't recognize campuses
        # Detect campuses by characteristic feature pattern and boost their AI scores
        # Campus profile: good green space, clean environment, low water, moderate/low buildings
        is_campus = (
            features.get('green_area_ratio', 0) > 0.45 and      # Good green space
            features.get('environmental_quality', 0) > 0.70 and # Clean/well-maintained
            features.get('water_proximity', 0) < 0.25 and       # No nearby water (inland campus)
            features.get('building_density', 0) < 0.80          # Not overly dense
        )
        
        if is_campus and ai_score < 70:
            # Campus detected with low AI score (model doesn't understand campus features)
            # Boost towards traditional score for better balanced final score
            campus_boost = (traditional_score - ai_score) * 0.5  # Boost by 50% of gap
            ai_score = min(ai_score + campus_boost, traditional_score - 5)  # Don't exceed traditional -5
            logger.info(f"Campus location detected: boosted AI score +{campus_boost:.1f} ({ai_score:.2f})")
        
        signal_strength = _data_signal_strength(features)
        # Keep AI as an assistant model; reduce its influence when direct map
        # signals are sparse (common in heritage villages and rural terrain).
        ai_weight = 0.10 + 0.20 * signal_strength
        traditional_weight = 1.0 - ai_weight
        final_score = traditional_score * traditional_weight + ai_score * ai_weight
        ai_explanations = ai_result.get('feature_importance', {}).get('explanations', [])
    else:
        final_score = traditional_score
        ai_score = None
        ai_explanations = []
    
    # Apply Yin-Yang and Five Elements modifiers
    final_score = apply_feng_shui_modifiers(
        final_score,
        yin_yang_balance,
        five_elements['overall_score'],
        features,
        qi_flow_score
    )

    local_model_score = final_score
    deepseek_score = None
    deepseek_similarity_pct = None
    deepseek_alignment_applied = False
    deepseek_confidence = None
    deepseek_reason = None
    deepseek_model = None
    deepseek_category_scores: Dict[str, float] = {}

    # Ask DeepSeek for an independent score only when low-latency budget allows it.
    deepseek_alignment_enabled = bool(getattr(config, 'DEEPSEEK_ALIGNMENT_ENABLED', False))
    scoring_budget_sec = max(0.8, float(getattr(config, 'SCORING_MAX_LATENCY_SEC', 8.0)))
    elapsed_before_alignment = time.monotonic() - score_start_ts
    remaining_budget = scoring_budget_sec - elapsed_before_alignment

    if deepseek_alignment_enabled and remaining_budget > 0.9:
        try:
            from .chatbot_service import get_chatbot

            configured_timeout = max(0.8, float(getattr(config, 'DEEPSEEK_SCORE_TIMEOUT_SEC', 2.2)))
            deepseek_timeout = min(configured_timeout, max(0.8, remaining_budget - 0.2))

            score_context = {
                'features': {k: round(float(v), 4) for k, v in features.items() if isinstance(v, (int, float))},
                'category_scores': {k: round(float(v), 2) for k, v in category_scores.items()},
                'local_model_score': round(local_model_score, 2),
                'traditional_score': round(traditional_score, 2),
                'ai_score': round(ai_score, 2) if ai_score is not None else None,
                'yin_yang_balance': round(yin_yang_balance, 2),
                'five_elements_harmony': round(five_elements.get('overall_score', 0.0), 2),
                'qi_flow_score': round(qi_flow_score, 2),
                'location_context': {
                    'address': (location_context or {}).get('address', ''),
                    'latitude': (location_context or {}).get('latitude'),
                    'longitude': (location_context or {}).get('longitude'),
                    'radius': (location_context or {}).get('radius'),
                },
            }

            deepseek_result = get_chatbot().get_deepseek_score(score_context, timeout_sec=deepseek_timeout)
            if deepseek_result.get('success'):
                parsed_deepseek = deepseek_result.get('overall_score')
                if isinstance(parsed_deepseek, (int, float)):
                    deepseek_score = max(0.0, min(100.0, float(parsed_deepseek)))
                    deepseek_model = deepseek_result.get('model')
                    deepseek_confidence = deepseek_result.get('confidence')
                    deepseek_reason = deepseek_result.get('reason')

                    # BALANCED SCORE BLEND: Fixed 65% local / 35% DeepSeek regardless of direction.
                    deepseek_alignment_factor = 0.35
                    final_score = local_model_score * (1.0 - deepseek_alignment_factor) + deepseek_score * deepseek_alignment_factor
                    score_difference = deepseek_score - local_model_score
                    logger.info(
                        f"✓ DeepSeek blend (35% weight): "
                        f"Local={local_model_score:.1f}, DeepSeek={deepseek_score:.1f} "
                        f"(diff={score_difference:+.1f}) → Final={final_score:.1f}"
                    )

                    deepseek_similarity_pct = max(0.0, 100.0 - abs(final_score - deepseek_score))
                    deepseek_alignment_applied = True

                    raw_deepseek_categories = deepseek_result.get('category_scores') or {}
                    if isinstance(raw_deepseek_categories, dict):
                        for key, value in raw_deepseek_categories.items():
                            if not isinstance(value, (int, float)):
                                continue
                            bounded = max(0.0, min(100.0, float(value)))
                            deepseek_category_scores[key] = bounded
                            if key in category_scores:
                                category_scores[key] = category_scores[key] * (1.0 - deepseek_alignment_factor) + bounded * deepseek_alignment_factor
            else:
                logger.warning(f"DeepSeek score unavailable: {deepseek_result.get('error', 'unknown')}")
        except Exception as deepseek_err:
            logger.warning(f"DeepSeek score alignment skipped: {deepseek_err}")
    elif not deepseek_alignment_enabled:
        logger.info("DeepSeek alignment disabled for low-latency scoring")
    else:
        logger.info(
            f"Skipping DeepSeek alignment to protect latency budget "
            f"({elapsed_before_alignment:.2f}s used of {scoring_budget_sec:.2f}s)"
        )
    
    # Generate explanations
    explanations = generate_explanations(features, category_scores, final_score)
    explanations.extend(ai_explanations)
    
    # Generate improvement suggestions
    suggestions = generate_improvement_suggestions(features, category_scores)
    
    result = {
        'final_score': round(final_score, 2),
        'traditional_score': round(traditional_score, 2),
        'ai_score': round(ai_score, 2) if ai_score else None,
        'ai_weight': round(ai_weight, 3) if ai_result else None,
        'category_scores': {k: round(v, 2) for k, v in category_scores.items()},
        'yin_yang_balance': round(yin_yang_balance, 2),
        'five_elements': {k: round(v, 2) for k, v in five_elements.items()},
        'qi_flow_score': round(qi_flow_score, 2),
        'deepseek_score': round(deepseek_score, 2) if isinstance(deepseek_score, (int, float)) else None,
        'deepseek_alignment_applied': deepseek_alignment_applied,
        'deepseek_confidence': round(deepseek_confidence, 2) if isinstance(deepseek_confidence, (int, float)) else None,
        'deepseek_similarity_pct': round(deepseek_similarity_pct, 2) if isinstance(deepseek_similarity_pct, (int, float)) else None,
        'deepseek_model': deepseek_model,
        'explanations': explanations,
        'suggestions': suggestions
    }

    result['timings'] = {
        'scoring_ms': round((time.monotonic() - score_start_ts) * 1000),
    }
    
    logger.info(f"Final Feng Shui score: {result['final_score']:.2f} (Traditional: {traditional_score:.2f}, AI: {ai_score})")
    return result


def calculate_green_space_score(features: Dict) -> float:
    """Calculate green space category score (0-100)."""
    ratio = _clamp01(features.get('green_area_ratio', 0.0))
    ndvi_coverage = features.get('ndvi_vegetation_coverage', None)
    density = _clamp01(features.get('building_density', 0.0))
    topography = _clamp01(features.get('topography_score', 0.5))
    rural_factor = _rural_context_factor(features)

    # NDVI available: use satellite data (most accurate)
    if ndvi_coverage is not None:
        # Satellite vegetation is ground truth
        satellite_score = float(ndvi_coverage) * 100.0
        return max(0.0, min(satellite_score, 100.0))

    # NDVI unavailable: standard fallback
    if ratio > 0.05:
        urban_score = min(ratio / 0.30 * 100.0, 100.0)
    else:
        openness_score = (1.0 - density) * 100.0
        topology_bonus = topography * 30.0
        urban_score = openness_score * 0.60 + topology_bonus * 0.40
    
    # Rural proxy: openness + terrain quality.
    natural_proxy = ((1.0 - density) * 0.60 + topography * 0.40) * 100.0

    score = max(urban_score, natural_proxy) * 0.70 + min(urban_score, natural_proxy) * 0.30
    return max(0.0, min(score, 100.0))


def calculate_water_score(features: Dict) -> float:
    """
    Calculate enhanced water element score (0-100).
    
    Now includes:
    - Water proximity and quality
    - Auspicious orientation (朝阳水)
    - Water flow characteristics
    - Traditional mountain-water relationship
    - Smart fallback when satellite/POI data unavailable
    """
    proximity = _clamp01(features.get('water_proximity', 0.0))
    hydrosheds_river = _clamp01(features.get('hydrosheds_river_proximity', 0.5))
    flood_risk = _clamp01(features.get('flood_risk_index', 0.5))
    topography = _clamp01(features.get('topography_score', 0.5))
    aspect_degrees = features.get('aspect_degrees')
    latitude = features.get('latitude', 30.0)
    rural_factor = _rural_context_factor(features)

    # TIER 1: Enhanced water quality assessment
    water_quality = _calculate_water_quality_proxy(hydrosheds_river, flood_risk)
    
    # TIER 1: Auspicious water orientation (朝阳水)
    water_direction_score = _get_water_direction_score(latitude, features.get('longitude', 0.0), aspect_degrees)
    
    # Blend AMap water POIs with HydroSHEDS river network signal
    flood_safety = 1 - min(max(flood_risk, 0.0), 1.0)
    
    urban_combined = proximity * 0.50 + hydrosheds_river * 0.30 + flood_safety * 0.20
    rural_combined = hydrosheds_river * 0.55 + flood_safety * 0.25 + topography * 0.20

    base_water_score = max(urban_combined, rural_combined) * 0.70 + min(urban_combined, rural_combined) * 0.30
    
    # Apply water quality enhancement (TIER 1)
    quality_boost = water_quality * 0.15  # 15% boost for premium quality
    direction_boost = water_direction_score * 0.10  # 10% boost for auspicious direction
    
    final_water_score = base_water_score + quality_boost + direction_boost
    
    # Log water analysis details
    logger.info(
        f"✓ Water analysis: proximity={proximity:.2f}, river_network={hydrosheds_river:.2f}, "
        f"quality={water_quality:.2f}(+{quality_boost:.2f}), direction={water_direction_score:.2f}(+{direction_boost:.2f}), "
        f"flood_safety={flood_safety:.2f} → score={final_water_score * 100.0:.1f}/100"
    )
    
    return max(0.0, min(final_water_score * 100.0, 100.0))


def calculate_building_score(features: Dict) -> float:
    """Calculate building harmony score (0-100)."""
    density = _clamp01(features.get('building_density', 0.0))
    harmony = _clamp01(features.get('building_harmony', 0.5))
    height_variance = _clamp01(features.get('building_height_variance', 0.5))

    # Prefer balanced built form: moderate heights, lower obstruction, better harmony.
    score = ((1.0 - density) * 0.55 + harmony * 0.35 + (1.0 - height_variance) * 0.10) * 100.0
    return max(0.0, min(score, 100.0))


def calculate_road_score(features: Dict) -> float:
    """Calculate road accessibility score (0-100)."""
    density = _clamp01(features.get('road_intersection_density', 0.0))
    rural_factor = _rural_context_factor(features)

    # Moderate density is best; sparse rural areas should not collapse to zero.
    if density < 0.05:
        score = 40.0
    elif density < 0.3:
        score = 40.0 + (density - 0.05) / 0.25 * 35.0
    elif density < 0.7:
        score = 75.0 + (density - 0.3) / 0.4 * 25.0
    else:
        score = 100.0 - (density - 0.7) / 0.3 * 30.0

    if rural_factor > 0.5 and density < 0.15:
        score = max(score, 55.0)

    return max(0.0, min(score, 100.0))


def calculate_orientation_category_score(features: Dict) -> float:
    """Calculate orientation category score (0-100)."""
    orientation = _clamp01(features.get('orientation_score', 0.5))
    topography = _clamp01(features.get('topography_score', 0.5))
    total_buildings = _clamp01(features.get('total_buildings_nearby', 0.0))
    rural_factor = _rural_context_factor(features)

    base = orientation * 100.0
    if rural_factor > 0.5 and total_buildings < 0.1:
        natural_orientation = (orientation * 0.5 + topography * 0.5) * 100.0
        return max(base, natural_orientation)

    return base


def calculate_environment_score(features: Dict) -> float:
    """
    Calculate enhanced environmental quality score (0-100).
    
    Now includes:
    - Proximity to services (hospitals, schools)
    - Air quality proxy (green space, density, environment)
    - Noise pollution assessment
    - Sunlight exposure quality
    """
    quality = _clamp01(features.get('environmental_quality', 0.0))
    topography = _clamp01(features.get('topography_score', 0.5))
    flood_safety = 1.0 - _clamp01(features.get('flood_risk_index', 0.5))
    qi_flow = _clamp01(features.get('qi_flow', 0.5))
    openness = 1.0 - _clamp01(features.get('building_density', 0.0))
    rural_factor = _rural_context_factor(features)
    
    # TIER 1: Enhanced environmental metrics
    green = _clamp01(features.get('green_area_ratio', 0.0))
    density = _clamp01(features.get('building_density', 0.0))
    road_density = _clamp01(features.get('road_intersection_density', 0.0))
    
    air_quality_score = _estimate_air_quality_from_features(quality, green, density)
    noise_score = 1.0 - _estimate_noise_level_from_features(road_density, density)
    sunlight_score = _estimate_sunlight_exposure(
        features.get('aspect_degrees'), 
        features.get('latitude', 30.0),
        density
    )

    urban_score = quality * 100.0
    
    # Enhanced natural support with air/noise/light metrics
    natural_support = (topography * 0.30 + flood_safety * 0.15 + qi_flow * 0.15 + 
                      openness * 0.10 + air_quality_score * 0.15 + 
                      noise_score * 0.10 + sunlight_score * 0.05) * 100.0
    
    blend = rural_factor * 0.75
    score = urban_score * (1.0 - blend) + max(urban_score, natural_support) * blend
    
    # Log environmental analysis details
    logger.info(
        f"✓ Environmental analysis: quality={quality:.2f}, air={air_quality_score:.2f}, "
        f"noise={noise_score:.2f}, sunlight={sunlight_score:.2f}, "
        f"topo={topography:.2f}, flood_safety={flood_safety:.2f} → score={score:.1f}/100"
    )
    
    return max(0.0, min(score, 100.0))


def calculate_spiritual_score(features: Dict) -> float:
    """
    Calculate spiritual energy score (0-100).
    
    Spiritual energy comes from two sources:
    1. Intrinsic spiritual quality: QI flow, orientation, environmental harmony
    2. Sanctified spaces: Temples and religious sites (bonus, not primary)
    
    KEY CHANGE: Don't penalize locations for lacking temples. Instead, calculate
    the natural spiritual energy of the place based on its environmental quality,
    then boost if temples are present.
    """
    # Temple presence as a bonus
    temple_presence = _clamp01(features.get('spiritual_presence', 0.0))
    
    # Intrinsic spiritual quality factors
    qi_flow = _clamp01(features.get('qi_flow', 0.5))
    orientation = _clamp01(features.get('orientation_score', 0.5))
    topography = _clamp01(features.get('topography_score', 0.5))
    environmental = _clamp01(features.get('environmental_quality', 0.5))
    green = _clamp01(features.get('green_area_ratio', 0.5))
    
    # Base spiritual quality from environmental harmony
    # High QI flow + good orientation + green space = naturally spiritual
    spiritual_quality = (qi_flow * 0.35 + 
                        orientation * 0.35 + 
                        environmental * 0.20 + 
                        green * 0.10)  # % for natural harmony
    
    # Convert quality to score (0-100)
    if spiritual_quality > 0.80:
        base_score = 75 + (spiritual_quality - 0.70) * 20  # 75-100 range
    elif spiritual_quality > 0.70:
        base_score = 70 + (spiritual_quality - 0.65) * 10  # 70-75 range
    elif spiritual_quality > 0.60:
        base_score = 60 + (spiritual_quality - 0.55) * 10  # 60-70 range
    else:
        base_score = 50 + spiritual_quality * 20           # 50-60 range for below average
    
    # Temple presence adds to spiritual energy (not replaces)
    temple_bonus = 0.0
    if temple_presence > 0.0:
        # Having temples nearby boosts spiritual score
        # 1 temple (presence=0.5) adds +10 points
        # 2+ temples (presence=1.0) adds +15 points
        temple_bonus = temple_presence * 15
    
    final_score = base_score + temple_bonus
    
    return max(0.0, min(final_score, 100.0))


def generate_explanations(features: Dict, 
                         category_scores: Dict,
                         final_score: float) -> List[str]:
    """
    Generate human-readable explanations for the Feng Shui analysis.
    
    Args:
        features: Extracted features
        category_scores: Category scores
        final_score: Final weighted score
    
    Returns:
        List of explanation strings
    """
    explanations = []
    
    # Overall assessment
    if final_score >= 80:
        explanations.append(
            "🌟 This location has excellent Feng Shui characteristics with strong positive energy flow."
        )
    elif final_score >= 60:
        explanations.append(
            "✨ This location has good Feng Shui with favorable environmental balance."
        )
    elif final_score >= 40:
        explanations.append(
            "⚖️ This location has average Feng Shui with mixed positive and negative influences."
        )
    else:
        explanations.append(
            "⚠️ This location has challenging Feng Shui characteristics that may benefit from remedies."
        )
    
    # Green space analysis
    green_score = category_scores['green_space']
    if green_score >= 70:
        explanations.append(
            f"🌳 Excellent green space coverage ({green_score:.0f}/100) promotes vitality and fresh chi energy."
        )
    elif green_score >= 40:
        explanations.append(
            f"🌿 Moderate green space presence ({green_score:.0f}/100) provides adequate natural balance."
        )
    else:
        explanations.append(
            f"🏙️ Limited green space ({green_score:.0f}/100). Consider adding plants or visiting nearby parks regularly."
        )
    
    # Water element analysis
    water_score = category_scores['water_element']
    river_signal = features.get('hydrosheds_river_proximity', 0.5)
    flood_risk = features.get('flood_risk_index', 0.5)
    if water_score >= 70:
        explanations.append(
            f"💧 Water element is well-positioned ({water_score:.0f}/100), bringing prosperity and wealth energy."
        )
    elif water_score >= 40:
        explanations.append(
            f"🌊 Water element is present ({water_score:.0f}/100) but could be optimized for better flow."
        )
    else:
        explanations.append(
            f"🏜️ Water element is distant ({water_score:.0f}/100). Consider water features to enhance energy."
        )

    if river_signal >= 0.65:
        explanations.append(
            "🌊 HydroSHEDS river-network analysis indicates strong natural flow channels nearby, supporting smoother Qi circulation."
        )
    elif river_signal <= 0.35:
        explanations.append(
            "🧭 HydroSHEDS indicates weaker river-network influence nearby; consider symbolic or designed water elements to strengthen flow balance."
        )

    if flood_risk >= 0.70:
        explanations.append(
            "⚠️ Flood-risk signal is elevated; prioritize drainage design, waterflow redirection, and protective landscape planning."
        )
    elif flood_risk <= 0.35:
        explanations.append(
            "✅ Flood-risk signal is relatively low, supporting more stable long-term site balance."
        )
    
    # Building harmony
    building_score = category_scores['building_harmony']
    if building_score >= 70:
        explanations.append(
            f"🏘️ Building density is balanced ({building_score:.0f}/100), allowing energy to flow freely."
        )
    elif building_score >= 40:
        explanations.append(
            f"🏢 Building density is moderate ({building_score:.0f}/100) with acceptable energy circulation."
        )
    else:
        explanations.append(
            f"🌆 High building density ({building_score:.0f}/100) may restrict energy flow. Ensure good ventilation."
        )
    
    # Orientation
    orientation_score = category_scores['orientation']
    if orientation_score >= 70:
        explanations.append(
            f"🧭 Building orientations are favorable ({orientation_score:.0f}/100) for capturing positive energy."
        )
    elif orientation_score < 50:
        explanations.append(
            f"🔄 Building orientations could be improved ({orientation_score:.0f}/100). Use mirrors or adjustments."
        )
    
    # Environmental quality
    env_score = category_scores['environment']
    if env_score >= 60:
        explanations.append(
            f"🏥 Good access to essential services ({env_score:.0f}/100) supports overall wellbeing."
        )
    
    # Spiritual energy
    spiritual_score = category_scores['spiritual_energy']
    if spiritual_score >= 60:
        explanations.append(
            f"🕉️ Spiritual presence is strong ({spiritual_score:.0f}/100), providing grounding energy."
        )
    
    return explanations


def calculate_yin_yang_balance(features: Dict, category_scores: Dict) -> float:
    """
    Calculate Yin-Yang balance score.
    
    Yin elements: Water, stillness, green spaces
    Yang elements: Buildings, roads, activity
    
    Perfect balance = 100, complete imbalance = 0
    
    Smart fallback: When satellite data (NDVI/HydroSHEDS) is unavailable,
    estimate Yin presence from density/topography to avoid artificial imbalance.
    
    Args:
        features: Extracted features
        category_scores: Category scores
    
    Returns:
        Yin-Yang balance score (0-100)
    """
    green = _clamp01(features.get('green_area_ratio', 0.0))
    water = _clamp01(features.get('water_proximity', 0.0))
    
    # Yin score (calm, natural elements)
    yin_score = (
        green * 0.30 +
        water * 0.30 +
        _clamp01(features.get('spiritual_presence', 0.0)) * 0.15 +
        _clamp01(features.get('topography_score', 0.5)) * 0.25
    )
    
    # Yang score (active, built elements)
    yang_score = (
        _clamp01(features.get('building_density', 0.0)) * 0.35 +
        _clamp01(features.get('road_intersection_density', 0.0)) * 0.35 +
        _clamp01(features.get('qi_flow', 0.5)) * 0.20 +
        _clamp01(features.get('wind_exposure_score', 0.5)) * 0.10
    )

    total_energy = yin_score + yang_score
    if total_energy < 0.12:
        # Sparse-data fallback: treat as moderately balanced rather than pathological zero.
        balance_score = 68.0
        logger.info(f"Yin-Yang balance: {balance_score:.2f} (sparse-energy fallback, Yin: {yin_score:.2f}, Yang: {yang_score:.2f})")
        return balance_score
    
    # Calculate balance (closer to 0.5 = better balance)
    balance_ratio = yin_score / (total_energy + 0.001)  # Avoid division by zero
    
    # Score balance: optimal ratio is 0.4-0.6
    deviation = abs(balance_ratio - 0.5) * 2  # 0-1 scale
    balance_score = (1 - deviation) * 100
    balance_score = max(35.0, min(100.0, balance_score))
    
    logger.info(f"Yin-Yang balance: {balance_score:.2f} (Yin: {yin_score:.2f}, Yang: {yang_score:.2f})")
    return balance_score


def calculate_five_elements(features: Dict, category_scores: Dict) -> Dict:
    """
    Calculate Five Elements (Wu Xing) harmony score.
    
    Five Elements:
    - Wood: Green spaces, growth
    - Fire: Orientation, sun exposure
    - Earth: Buildings, stability
    - Metal: Roads, structure
    - Water: Water bodies, flow
    
    Args:
        features: Extracted features
        category_scores: Category scores
    
    Returns:
        Dictionary with individual element scores and overall harmony
    """
    green_ratio = _clamp01(features.get('green_area_ratio', 0.0))
    building_density = _clamp01(features.get('building_density', 0.0))
    topography = _clamp01(features.get('topography_score', 0.5))
    orientation = _clamp01(features.get('orientation_score', 0.5))
    water_proximity = _clamp01(features.get('water_proximity', 0.0))
    hydrosheds = _clamp01(features.get('hydrosheds_river_proximity', 0.5))
    flood_safety = 1.0 - _clamp01(features.get('flood_risk_index', 0.5))
    wind_dir = _clamp01(features.get('wind_direction_favorability', 0.5))
    wind_exposure = _clamp01(features.get('wind_exposure_score', 0.5))
    rural_factor = _rural_context_factor(features)

    # Wood element (growth, vitality)
    wood_direct = green_ratio * 100.0
    wood_proxy = ((1.0 - building_density) * 0.65 + topography * 0.20 + rural_factor * 0.15) * 100.0
    wood_score = max(wood_direct, wood_proxy)
    
    # Fire element (energy, light)
    fire_score = (orientation * 0.70 + wind_dir * 0.30) * 100.0
    
    # Earth element (stability, grounding)
    earth_score = max(float(category_scores.get('building_harmony', 50.0)), topography * 90.0)
    
    # Metal element (structure, organization)
    road_score = float(category_scores.get('road_accessibility', 50.0))
    metal_proxy = (wind_exposure * 0.40 + (1.0 - building_density) * 0.20 + 0.40) * 100.0
    metal_score = max(road_score, min(metal_proxy, 100.0))
    
    # Water element (flow, wealth)
    water_direct = water_proximity * 100.0
    water_proxy = (hydrosheds * 0.55 + flood_safety * 0.25 + topography * 0.20) * 100.0
    water_score = max(water_direct, water_proxy)
    
    # Calculate harmony (balance among all elements)
    element_scores = [wood_score, fire_score, earth_score, metal_score, water_score]
    avg_score = sum(element_scores) / len(element_scores)
    
    # Penalty for extreme imbalance
    variance = sum((score - avg_score) ** 2 for score in element_scores) / len(element_scores)
    std_dev = math.sqrt(variance)
    
    # Lower standard deviation = better harmony
    harmony_penalty = min(std_dev / 35, 1.0)  # Normalize
    overall_harmony = avg_score * (1 - harmony_penalty * 0.2)
    
    logger.info(f"Five Elements harmony: {overall_harmony:.2f}")
    
    return {
        'wood': wood_score,
        'fire': fire_score,
        'earth': earth_score,
        'metal': metal_score,
        'water': water_score,
        'overall_score': overall_harmony
    }


def calculate_qi_flow(features: Dict, category_scores: Dict) -> float:
    """
    Calculate Qi (energy) flow score.
    
    Good Qi flow requires:
    - Not too dense (allows movement)
    - Good orientation (captures positive energy)
    - Balance between open and enclosed spaces
    
    Args:
        features: Extracted features
        category_scores: Category scores
    
    Returns:
        Qi flow score (0-100)
    """
    # Factors affecting Qi flow
    
    # 1. Building density (too high blocks Qi)
    density = _clamp01(features.get('building_density', 0.0))
    density_score = (1 - density) * 100
    
    # 2. Road network (facilitates Qi circulation)
    road_score = category_scores.get('road_accessibility', 50)
    
    # 3. Green spaces (generate positive Qi)
    green_score = category_scores.get('green_space', 50)
    
    # 4. Water (channels Qi)
    water_score = category_scores.get('water_element', 50)
    
    # Weighted combination
    extracted_qi = _clamp01(features.get('qi_flow', 0.5)) * 100.0
    topography = _clamp01(features.get('topography_score', 0.5)) * 100.0
    rural_factor = _rural_context_factor(features)

    qi_flow = (
        density_score * 0.25 +
        road_score * 0.15 +
        green_score * 0.20 +
        water_score * 0.15 +
        extracted_qi * 0.25
    )

    # For sparse contexts, preserve positive natural-flow signals.
    if rural_factor > 0.5 and qi_flow < 55:
        qi_flow = max(qi_flow, extracted_qi * 0.7 + topography * 0.15 + 18.0)
    
    logger.info(f"Qi flow score: {qi_flow:.2f}")
    return max(0.0, min(qi_flow, 100.0))


def apply_feng_shui_modifiers(base_score: float,
                              yin_yang_balance: float,
                              five_elements_harmony: float,
                              features: Dict,
                              qi_flow_score: float) -> float:
    """
    Apply Yin-Yang and Five Elements modifiers to base score.
    
    Args:
        base_score: Base Feng Shui score
        yin_yang_balance: Yin-Yang balance score
        five_elements_harmony: Five Elements harmony score
    
    Returns:
        Modified final score
    """
    # Apply harmony modifiers (each can boost or reduce score by up to 10%).
    yin_yang_modifier = (yin_yang_balance / 100 - 0.5) * 0.1
    elements_modifier = (five_elements_harmony / 100 - 0.5) * 0.1

    # Natural-terrain modifier: high terrain quality is a core traditional
    # Feng Shui signal for many historical villages and mountain-water sites.
    topography_score = _clamp01(features.get('topography_score', 0.5))
    topography_modifier = (topography_score - 0.5) * 0.16

    # Qi-flow modifier from the composite category score.
    qi_modifier = ((_clamp01(qi_flow_score / 100.0)) - 0.5) * 0.12

    total_modifier = yin_yang_modifier + elements_modifier + topography_modifier + qi_modifier
    total_modifier = max(-0.22, min(0.22, total_modifier))
    
    modified_score = base_score * (1 + total_modifier)
    
    # Ensure score stays in valid range
    return max(0, min(modified_score, 100))


def generate_improvement_suggestions(features: Dict, category_scores: Dict) -> List[str]:
    """
    Generate actionable improvement suggestions based on low-scoring factors.
    
    Args:
        features: Extracted features
        category_scores: Category scores
    
    Returns:
        List of suggestion strings
    """
    suggestions = []
    
    # Green space suggestions
    if category_scores.get('green_space', 100) < 50:
        suggestions.append(
            "🌱 Increase greenery: Add indoor plants, visit nearby parks regularly, "
            "or create a small garden to enhance Wood element and positive Qi."
        )
    
    # Water element suggestions
    if category_scores.get('water_element', 100) < 50:
        suggestions.append(
            "💧 Enhance water element: Place a small water fountain near the entrance, "
            "add an aquarium, or display water imagery to attract wealth energy."
        )
    
    # Building density suggestions
    if category_scores.get('building_harmony', 100) < 50:
        suggestions.append(
            "🏢 Improve space harmony: Use mirrors to create sense of openness, "
            "ensure good ventilation, and declutter to allow Qi to flow freely."
        )
    
    # Road accessibility suggestions
    road_score = category_scores.get('road_accessibility', 50)
    if road_score < 40:
        suggestions.append(
            "🚗 Improve accessibility: This area may be too isolated. "
            "Consider locations with better transportation connections."
        )
    elif road_score > 80:
        suggestions.append(
            "🔇 Reduce noise impact: High traffic density may bring excessive Yang energy. "
            "Use sound barriers, plants, or water features to create a buffer."
        )
    
    # Orientation suggestions
    if category_scores.get('orientation', 100) < 50:
        suggestions.append(
            "🧭 Optimize orientation: Use mirrors to redirect energy flow, "
            "place important furniture facing auspicious directions (south/southeast)."
        )
    
    # Environmental quality suggestions
    if category_scores.get('environment', 100) < 50:
        suggestions.append(
            "🏥 Enhance environment: Ensure access to healthcare and educational facilities. "
            "Choose locations with good community infrastructure."
        )
    
    # Spiritual energy suggestions
    if category_scores.get('spiritual_energy', 100) < 30:
        suggestions.append(
            "🙏 Strengthen spiritual energy: Display religious or spiritual symbols, "
            "practice meditation, or visit nearby temples to enhance spiritual connection."
        )
    
    # Yin-Yang balance suggestions
    yin_yang = category_scores.get('yin_yang_balance', 100)
    if yin_yang < 70:
        yin_ratio = features.get('green_area_ratio', 0) + features.get('water_proximity', 0)
        yang_ratio = features.get('building_density', 0) + features.get('road_intersection_density', 0)
        
        if yin_ratio < yang_ratio:
            suggestions.append(
                "☯️ Balance Yin-Yang: Too much Yang (activity) energy. "
                "Add calm elements like plants, water, and quiet spaces."
            )
        else:
            suggestions.append(
                "☯️ Balance Yin-Yang: Too much Yin (stillness) energy. "
                "Add active elements like bright lights and social activities."
            )
    
    # Five Elements harmony suggestions
    if category_scores.get('five_elements_harmony', 100) < 60:
        suggestions.append(
            "🌟 Harmonize Five Elements: Ensure presence of all five elements - "
            "Wood (plants), Fire (light), Earth (ceramics), Metal (decor), Water (fountains)."
        )
    
    # Qi flow suggestions
    if category_scores.get('qi_flow', 100) < 60:
        suggestions.append(
            "💨 Improve Qi flow: Remove obstacles blocking pathways, "
            "keep spaces clean and organized, ensure good air circulation."
        )
    
    # If score is already high, provide maintenance suggestions
    if not suggestions:
        suggestions.append(
            "✨ Excellent Feng Shui! Maintain this positive energy by keeping spaces clean, "
            "refreshing plants regularly, and practicing gratitude."
        )
    
    logger.info(f"Generated {len(suggestions)} improvement suggestions")
    return suggestions
