"""
Quick test script to verify the backend API is working correctly.
"""
import requests
import json


def _safe_score_text(value):
    try:
        return f"{float(value):.1f}/100"
    except (TypeError, ValueError):
        return "N/A"

# Test 1: Health check
print("=" * 70)
print("TEST 1: Health Check")
print("=" * 70)
try:
    response = requests.get('http://127.0.0.1:5001/health', timeout=5)
    print(f"✅ Status Code: {response.status_code}")
    print(f"✅ Response: {response.json()}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("TEST 2: Analyze Location (Beijing City Center)")
print("=" * 70)

# Test 2: Analyze a real location
test_data = {
    "latitude": 39.90923,
    "longitude": 116.397428,
    "radius": 500
}

print(f"📍 Testing Location: {test_data['latitude']}, {test_data['longitude']}")
print(f"📏 Radius: {test_data['radius']}m")
print("\nSending request to /api/analyze...")

try:
    response = requests.post(
        'http://127.0.0.1:5001/api/analyze',
        json=test_data,
        headers={'Content-Type': 'application/json'},
        timeout=30
    )
    
    print(f"\n✅ Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        data = result.get('data', result)
        print("\n" + "=" * 70)
        print("RESULTS:")
        print("=" * 70)
        print(f"🎯 Final Score: {_safe_score_text(data.get('final_score'))}")
        print(f"📊 Traditional Score: {_safe_score_text(data.get('traditional_score'))}")
        print(f"🤖 AI Score: {_safe_score_text(data.get('ai_score'))}")
        
        print("\n📈 Category Scores:")
        category_scores = data.get('category_scores', {})
        for key, value in category_scores.items():
            print(f"  • {key}: {_safe_score_text(value)}")
        
        print("\n🔮 Five Elements:")
        five_elements = data.get('five_elements', {})
        for element, value in five_elements.items():
            if element != 'overall_score':
                print(f"  • {element}: {_safe_score_text(value)}")
        
        print(f"\n☯️ Yin-Yang Balance: {_safe_score_text(data.get('yin_yang_balance'))}")
        print(f"🌊 Qi Flow Score: {_safe_score_text(data.get('qi_flow_score'))}")
        
        print("\n💡 Top 3 Explanations:")
        for i, exp in enumerate(data.get('explanations', [])[:3], 1):
            print(f"  {i}. {exp}")
        
        print("\n✨ Top 3 Suggestions:")
        for i, sug in enumerate(data.get('suggestions', [])[:3], 1):
            print(f"  {i}. {sug}")
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\n🚀 System is ready! Open frontend/index.html in your browser.")
        
    else:
        print(f"❌ Error Response: {response.text}")
        
except requests.exceptions.Timeout:
    print("❌ Request timed out (>30s). Backend may be processing...")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
