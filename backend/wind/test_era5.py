# Test script for ERA5 Wind Data Service
# Tests wind data fetching, direction analysis, and Feng Shui scoring

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from era5_service import ERA5WindService
from config import wind_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def test_wind_data_fetch():
    """Test fetching wind data for various locations."""
    
    test_locations = [
        {
            'name': '🌊 Beijing (Continental Climate)',
            'longitude': 116.4074,
            'latitude': 39.9042,
            'radius': 500
        },
        {
            'name': '🏝️ Shanghai (Coastal Area)',
            'longitude': 121.4737,
            'latitude': 31.2304,
            'radius': 500
        },
        {
            'name': '🏔️ Tibetan Plateau (High Altitude)',
            'longitude': 91.1,
            'latitude': 29.65,
            'radius': 500
        }
    ]
    
    print("\n" + "="*80)
    print("🌬️  ERA5 WIND DATA SERVICE TEST")
    print("="*80)
    
    # Initialize service
    try:
        service = ERA5WindService(wind_config.GEE_SERVICE_ACCOUNT_PATH)
        print(f"✓ ERA5WindService initialized")
        print(f"  Service enabled: {service.enabled}")
        print(f"  GEE authenticated: {service._authenticated}")
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return
    
    for location in test_locations:
        print(f"\n{'='*80}")
        print(f"📍 {location['name']}")
        print(f"   Coordinates: ({location['latitude']:.4f}, {location['longitude']:.4f})")
        print(f"   Radius: {location['radius']}m")
        print(f"{'='*80}")
        
        # Fetch wind analysis
        result = service.get_wind_analysis(
            longitude=location['longitude'],
            latitude=location['latitude'],
            radius=location['radius']
        )
        
        if not result['success']:
            print(f"❌ Error: {result['error']}")
            continue
        
        metrics = result['wind_metrics']
        scores = result['feng_shui_scores']
        
        # Display wind metrics
        print(f"\n🌀 WIND METRICS:")
        print(f"   Average Speed: {metrics['avg_speed']:.2f} m/s ({metrics['speed_category'].upper()})")
        print(f"   Dominant Direction: {metrics['dominant_direction']} ({metrics['direction_degrees']:.1f}°)")
        print(f"   Favorability: {metrics['favorability'].upper()}")
        print(f"   Consistency: {metrics['consistency']:.3f} (0-1 scale)")
        print(f"   Speed Variance: {metrics['speed_variance']:.2f} m/s")
        
        # Display Feng Shui scores
        print(f"\n✨ FENG SHUI WIND SCORES:")
        print(f"   Overall Wind Score: {scores['overall_wind_score']:.1f}/100")
        print(f"   - Speed Optimality: {scores['speed_optimality_score']:.1f}/100")
        print(f"   - Direction Score: {scores['direction_score']:.1f}/100")
        print(f"   - Consistency Score: {scores['consistency_score']:.1f}/100")
        
        # Interpretation
        overall = scores['overall_wind_score']
        if overall >= 80:
            print(f"   ⭐ EXCELLENT: Ideal wind conditions for Feng Shui")
        elif overall >= 65:
            print(f"   ✓ GOOD: Favorable wind patterns")
        elif overall >= 50:
            print(f"   ~ FAIR: Acceptable wind conditions")
        else:
            print(f"   ⚠ WEAK: Suboptimal wind patterns")
        
        # Wind advice
        print(f"\n💡 FENG SHUI ADVICE:")
        
        # Speed advice
        speed = metrics['avg_speed']
        if speed < 1.5:
            print(f"   • Wind is too calm - consider features to promote air circulation")
        elif 1.5 <= speed <= 5.5:
            print(f"   • Wind speed is ideal - gentle breeze promotes good Qi flow")
        else:
            print(f"   • Wind is strong - consider windbreaks or sheltering features")
        
        # Direction advice
        direction = metrics['dominant_direction']
        if metrics['favorability'] == 'favorable':
            print(f"   • {direction} wind is favorable - warm and nurturing energy")
        elif metrics['favorability'] == 'neutral':
            print(f"   • {direction} wind is neutral - balanced energy")
        else:
            print(f"   • {direction} wind is challenging - consider protection from harsh winds")


def test_direction_calculation():
    """Test wind direction calculation from u/v components."""
    
    print("\n" + "="*80)
    print("🧭 WIND DIRECTION CALCULATION TEST")
    print("="*80)
    
    service = ERA5WindService(wind_config.GEE_SERVICE_ACCOUNT_PATH)
    
    test_cases = [
        (0, 5, "N", "North wind (from north)"),
        (5, 0, "E", "East wind (from east)"),
        (0, -5, "S", "South wind (from south)"),
        (-5, 0, "W", "West wind (from west)"),
        (3, 3, "NE", "Northeast wind"),
        (3, -3, "SE", "Southeast wind"),
        (-3, -3, "SW", "Southwest wind"),
        (-3, 3, "NW", "Northwest wind"),
    ]
    
    print("\n🔍 Testing wind direction from U/V components:")
    for u, v, expected_dir, description in test_cases:
        wind_data = {
            'u_mean': u,
            'v_mean': v,
            'u_std': 0.5,
            'v_std': 0.5,
            'seasonal': {}
        }
        metrics = service._calculate_wind_metrics(wind_data)
        
        speed = metrics['avg_speed']
        direction = metrics['dominant_direction']
        degrees = metrics['direction_degrees']
        
        match = "✓" if direction == expected_dir else "✗"
        print(f"   {match} U={u:+.1f}, V={v:+.1f} → {direction} ({degrees:.1f}°) "
              f"[speed={speed:.1f} m/s] - {description}")


def test_feng_shui_scoring():
    """Test Feng Shui scoring logic."""
    
    print("\n" + "="*80)
    print("⚖️  FENG SHUI SCORING TEST")
    print("="*80)
    
    service = ERA5WindService(wind_config.GEE_SERVICE_ACCOUNT_PATH)
    
    test_scenarios = [
        {
            'name': 'Ideal Conditions',
            'speed': 3.0,
            'direction': 'SE',
            'consistency': 0.8
        },
        {
            'name': 'Too Calm',
            'speed': 0.5,
            'direction': 'S',
            'consistency': 0.9
        },
        {
            'name': 'Too Strong',
            'speed': 12.0,
            'direction': 'E',
            'consistency': 0.6
        },
        {
            'name': 'Unfavorable Direction',
            'speed': 4.0,
            'direction': 'N',
            'consistency': 0.7
        },
    ]
    
    print("\n🧪 Testing different wind scenarios:")
    for scenario in test_scenarios:
        # Create mock metrics
        favorability = service._get_direction_favorability(scenario['direction'])
        metrics = {
            'avg_speed': scenario['speed'],
            'dominant_direction': scenario['direction'],
            'favorability': favorability,
            'consistency': scenario['consistency']
        }
        
        scores = service._calculate_feng_shui_wind_scores(metrics)
        
        print(f"\n   Scenario: {scenario['name']}")
        print(f"     Speed: {scenario['speed']} m/s, "
              f"Direction: {scenario['direction']}, "
              f"Consistency: {scenario['consistency']:.1f}")
        print(f"     Overall Score: {scores['overall_wind_score']:.1f}/100")
        print(f"       - Speed: {scores['speed_optimality_score']:.1f}")
        print(f"       - Direction: {scores['direction_score']:.1f}")
        print(f"       - Consistency: {scores['consistency_score']:.1f}")


if __name__ == '__main__':
    print("\n🚀 Starting ERA5 Wind Service Tests...\n")
    
    try:
        # Run tests
        test_direction_calculation()
        test_feng_shui_scoring()
        test_wind_data_fetch()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        logger.exception(e)
        sys.exit(1)
