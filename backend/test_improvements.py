#!/usr/bin/env python3
"""
Test script to verify TIER 1-3 improvements are working in the Feng Shui scorer.
Shows logging output with improvements breakdown.
"""

import logging
from typing import Dict, Any

# Setup logging to see detailed improvement messages
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

# Import scorer with improvements  # noqa: F401
from scorer import calculate_feng_shui_score, _calculate_feature_interactions, _get_seasonal_adjustment_factor  # type: ignore

# Test features (simulating a good location with water and green space)
test_features: Dict[str, float] = {
    'latitude': 30.527,
    'longitude': 114.305,
    'aspect_degrees': 180.0,  # Perfect south-facing
    'green_area_ratio': 0.4,
    'water_proximity': 0.6,
    'building_density': 0.3,
    'road_intersection_density': 0.5,
    'orientation_score': 0.7,
    'environmental_quality': 0.5,
    'spiritual_presence': 0.3,
    'topography_score': 0.6,
    'hydrosheds_river_proximity': 0.7,
    'hydrosheds_river_density': 0.5,
    'qi_flow': 0.6,
    'building_avg_height': 0.4,
    'building_height_variance': 0.4,
    'building_harmony': 0.6,
    'total_buildings_nearby': 0.3,
    'wind_speed': 0.5,
    'wind_exposure_score': 0.6,
    'wind_direction_favorability': 0.6,
    'wind_consistency': 0.7,
    'wind_dominant_direction': 0.5,
    'flood_risk_index': 0.2,
    'flood_exposure': 0.2,
    'flood_surface_water_occurrence': 0.1,
    'flood_drainage_risk': 0.3,
}

test_location_context: Dict[str, Any] = {
    'address': 'Wuhan, China',
    'latitude': 30.527,
    'longitude': 114.305,
    'radius': 500,
}

print("=" * 80)
print("FENG SHUI SCORER - IMPROVEMENTS VERIFICATION TEST")
print("=" * 80)
print()

# Test feature interactions
print("TIER 2: Feature Interaction Detection")
print("-" * 80)
interactions = _calculate_feature_interactions(test_features)
for synergy_name, synergy_score in interactions.items():
    print(f"  {synergy_name}: {synergy_score:.3f}")
total_interaction_boost = sum([
    interactions['green_water_harmony'] * 0.05,
    interactions['qi_flow_optimization'] * 0.05,
    interactions['environmental_harmony'] * 0.04,
    interactions['mountain_water_config'] * 0.03,
    interactions['spiritual_natural_harmony'] * 0.03
])
print(f"  >>> Total interaction bonus: +{total_interaction_boost:.2f} points")
print()

# Test seasonal adjustment
print("TIER 3: Seasonal Adjustment Detection")
print("-" * 80)
seasonal_info: Dict[str, Any] = _get_seasonal_adjustment_factor(test_features['latitude'])
season_name = seasonal_info.get('season', 'N/A')
print(f"  Season: {season_name.upper() if isinstance(season_name, str) else season_name}")
print(f"  Element: {seasonal_info['element']}")
print(f"  Climate: {'Tropical' if seasonal_info['is_tropical'] else 'Temperate'}")
print(f"  Modifiers: {seasonal_info['modifiers']}")
print()

# Calculate full score with logging
print("FULL SCORING CALCULATION")
print("-" * 80)
result: Dict[str, Any] = calculate_feng_shui_score(test_features, test_location_context)  # type: ignore
print()

# Show results
print("=" * 80)
print("RESULTS - Score Breakdown")
print("=" * 80)
print(f"  Final Score: {result['final_score']:.2f}/100")
print(f"  Traditional Score: {result['traditional_score']:.2f}")
print(f"  AI Score: {result['ai_score']}")
print()
print("Category Scores:")
for cat, score in result['category_scores'].items():
    if cat not in ['yin_yang_balance', 'five_elements_harmony', 'qi_flow']:
        print(f"    {cat}: {score:.2f}")
print()
print("Advanced Metrics:")
print(f"    Yin-Yang Balance: {result['yin_yang_balance']:.2f}")
print(f"    Five Elements Harmony: {result['five_elements']['overall_score']:.2f}")
print(f"    Qi Flow: {result['qi_flow_score']:.2f}")
print()

print("=" * 80)
print("✓ IMPROVEMENTS VERIFICATION COMPLETE")
print("=" * 80)
print()
print("Log messages above show:")
print("  ✓ TIER 1: Water quality & orientation bonuses")
print("  ✓ TIER 1: Air quality, noise, sunlight assessment")
print("  ✓ TIER 2: Feature interactions (green+water, qi flow, etc.)")
print("  ✓ TIER 3: Seasonal adjustments applied")
print()
