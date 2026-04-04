# Test script for Buildings Data Service
# Tests building data fetching, height estimation, and Feng Shui harmony scoring

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from buildings_service import buildings_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def test_building_data_fetch():
    """Test fetching building data for various locations."""
    
    test_locations = [
        {
            'name': '🏢 Downtown Beijing (Wangfujing)',
            'longitude': 116.4074,
            'latitude': 39.9042,
            'radius': 500
        },
        {
            'name': '🌳 Green Park Area (Beijing)',
            'longitude': 116.4167,
            'latitude': 39.9833,
            'radius': 500
        },
        {
            'name': '🏗️ Industrial Zone',
            'longitude': 116.3500,
            'latitude': 39.8500,
            'radius': 500
        }
    ]
    
    print("\n" + "="*80)
    print("🏢 BUILDINGS DATA SERVICE TEST")
    print("="*80)
    
    for location in test_locations:
        print(f"\n{'='*80}")
        print(f"📍 {location['name']}")
        print(f"   Coordinates: ({location['latitude']:.4f}, {location['longitude']:.4f})")
        print(f"   Radius: {location['radius']}m")
        print(f"{'='*80}")
        
        # Fetch building data
        result = buildings_service.get_building_data(
            longitude=location['longitude'],
            latitude=location['latitude'],
            radius=location['radius']
        )
        
        if not result['success']:
            print(f"❌ Error: {result['error']}")
            continue
        
        buildings = result['buildings']
        metrics = result['metrics']
        
        # Display building metrics
        print(f"\n📊 BUILDING METRICS:")
        print(f"   Total Buildings: {metrics['total_buildings']}")
        print(f"   Average Height: {metrics['avg_height']:.1f}m")
        print(f"   Height Range: {metrics['min_height']:.1f}m - {metrics['max_height']:.1f}m")
        print(f"   Height Variance: {metrics['height_variance']:.1f}m")
        print(f"   Height Std Dev: {metrics['height_stddev']:.1f}m")
        print(f"   Building Density: {metrics['building_density']:.1f} buildings/km²")
        print(f"   Dominant Height: {metrics['dominant_height_category'].upper()}")
        
        # Display height category breakdown
        cats = metrics['height_categories']
        print(f"\n📐 HEIGHT DISTRIBUTION:")
        print(f"   Low (<10m):        {cats['low']:3d} buildings")
        print(f"   Medium (10-25m):   {cats['medium']:3d} buildings")
        print(f"   High (25-50m):     {cats['high']:3d} buildings")
        print(f"   Very High (50m+):  {cats['very_high']:3d} buildings")
        
        # Calculate harmony score
        harmony_score = buildings_service.calculate_building_harmony_score(metrics)
        
        print(f"\n✨ FENG SHUI HARMONY SCORE: {harmony_score:.2f}/1.00 ({harmony_score*100:.1f}%)")
        
        # Interpretation
        if harmony_score >= 0.8:
            print(f"   ⭐ EXCELLENT: Perfect building harmony!")
        elif harmony_score >= 0.65:
            print(f"   ✓ GOOD: Balanced building distribution")
        elif harmony_score >= 0.50:
            print(f"   ~ FAIR: Moderate building harmony")
        elif harmony_score >= 0.35:
            print(f"   ⚠ WEAK: Suboptimal building balance")
        else:
            print(f"   ❌ POOR: Chaotic or sparse building distribution")
        
        # Show top 10 buildings
        if buildings:
            print(f"\n🏢 TOP 10 NEAREST BUILDINGS:")
            sorted_buildings = sorted(buildings, key=lambda x: x['distance'])[:10]
            
            for i, building in enumerate(sorted_buildings, 1):
                print(f"\n   {i}. {building['name']}")
                print(f"      Type: {building['type']}")
                print(f"      Height: {building['height']:.1f}m")
                print(f"      Distance: {building['distance']:.1f}m")
                print(f"      Address: {building['address']}")


def test_height_estimation():
    """Test building height estimation function."""
    
    print("\n" + "="*80)
    print("📏 HEIGHT ESTIMATION TEST")
    print("="*80)
    
    test_names = [
        "100-meter Building",
        "30-story Office Complex",
        "东方明珠电视塔 (Oriental Pearl, 468m)",
        "北京国贸中心 (China World Trade Center, 330m)",
        "住宅楼 (Residential Building)",
        "Standard Office Building",
    ]
    
    print("\n🔍 Testing height extraction from building names:")
    for name in test_names:
        height = buildings_service._extract_height_from_name(name)
        print(f"   '{name}'")
        print(f"      → Extracted height: {height}m" if height > 0 else "      → No height found (using default)")


def test_distance_calculation():
    """Test distance calculation."""
    
    print("\n" + "="*80)
    print("🗺️  DISTANCE CALCULATION TEST")
    print("="*80)
    
    # Beijing center to specific locations
    beijing_center = (39.9042, 116.4074)
    
    test_points = [
        (39.9042, 116.4074, "Beijing Center (0m reference)"),
        (39.9100, 116.4100, "100m away"),
        (40.0000, 116.5000, "~10km away"),
    ]
    
    print("\n📍 Calculating distances from Beijing center:")
    for lat, lon, description in test_points:
        dist = buildings_service._calculate_distance(
            beijing_center[1], beijing_center[0],
            lon, lat
        )
        print(f"   {description}: {dist:.1f}m")


if __name__ == '__main__':
    print("\n🚀 Starting Buildings Data Service Tests...\n")
    
    try:
        # Run tests
        test_distance_calculation()
        test_height_estimation()
        test_building_data_fetch()
        
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
