"""
Test script to verify dynamic location-based scoring.
"""
import requests
import json

def test_location(name, lat, lng, radius=500):
    """Test a specific location and print results."""
    print(f"\n{'='*70}")
    print(f"TESTING: {name}")
    print(f"Coordinates: ({lat}, {lng}) | Radius: {radius}m")
    print('='*70)
    
    data = {
        "latitude": lat,
        "longitude": lng,
        "radius": radius
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:5001/api/analyze',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n🎯 FINAL SCORE: {result['final_score']:.1f}/100")
            print(f"   Traditional: {result['traditional_score']:.1f}")
            print(f"   AI: {result.get('ai_score', 'N/A'):.1f}")
            
            print(f"\n📊 CATEGORY SCORES:")
            cs = result['category_scores']
            print(f"   🌳 Green Space: {cs.get('green_space', 0):.1f}/100")
            print(f"   💧 Water Element: {cs.get('water_element', 0):.1f}/100")
            print(f"   🏢 Building Harmony: {cs.get('building_harmony', 0):.1f}/100")
            print(f"   🚗 Road Accessibility: {cs.get('road_accessibility', 0):.1f}/100")
            print(f"   🧭 Orientation: {cs.get('orientation', 0):.1f}/100")
            print(f"   🏥 Environment: {cs.get('environment', 0):.1f}/100")
            print(f"   🕉️  Spiritual Energy: {cs.get('spiritual_energy', 0):.1f}/100")
            
            return result['final_score']
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

# Test locations with different characteristics
print("\n" + "="*70)
print("DYNAMIC LOCATION SCORING VERIFICATION")
print("="*70)

scores = {}

# Test 1: Olympic Forest Park (should have HIGH green space and water)
scores['park'] = test_location(
    "Olympic Forest Park",
    lat=40.00265,
    lng=116.38850
)

# Test 2: Downtown Beijing (should have LOW green space, HIGH buildings)
scores['downtown'] = test_location(
    "Beijing Downtown (Wangfujing)",
    lat=39.91486,
    lng=116.40771
)

# Test 3: Suburban residential (should have MODERATE scores)
scores['suburban'] = test_location(
    "Suburban Residential Area",
    lat=39.98556,
    lng=116.32550
)

# Test 4: Near water (should have HIGH water element)
scores['water'] = test_location(
    "Near Houhai Lake",
    lat=39.93788,
    lng=116.38368
)

# Summary
print("\n" + "="*70)
print("SUMMARY - Scores should be DIFFERENT for different locations!")
print("="*70)
for name, score in scores.items():
    if score:
        print(f"{name:20} : {score:6.1f}/100")

print("\n" + "="*70)
if len(set([s for s in scores.values() if s])) > 1:
    print("✅ SUCCESS: Dynamic scoring is working! Different locations have different scores.")
else:
    print("❌ ISSUE: All locations have the same score. Check AMap API calls.")
print("="*70)
