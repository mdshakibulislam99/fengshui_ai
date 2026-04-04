"""
Direct test of AMap API calls to debug why POI searches are failing.
"""
import requests
import json
from config import config

print("=" * 70)
print("AMAP API DIRECT TEST")
print("=" * 70)

# Test 1: Check API key
print(f"\n1. API Key configured: {config.AMAP_API_KEY[:10]}...{config.AMAP_API_KEY[-5:]}")
print(f"   Key length: {len(config.AMAP_API_KEY)}")

# Test 2: Simple POI search
location = "116.397428,39.90923"  # Beijing city center
radius = 500

print(f"\n2. Testing POI search at {location}, radius {radius}m")

# Try parks category
params = {
    'key': config.AMAP_API_KEY,
    'location': location,
    'radius': radius,
    'types': '110100',  # Parks
    'offset': 50,
    'output': 'json'
}

print(f"\n3. Requesting: {config.AMAP_POI_SEARCH_URL}")
print(f"   Parameters: {json.dumps(params, indent=2)}")

try:
    response = requests.get(config.AMAP_POI_SEARCH_URL, params=params, timeout=10)
    print(f"\n4. Response Status: {response.status_code}")
    print(f"   Response URL: {response.url}")
    
    data = response.json()
    print(f"\n5. Response JSON:")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
    
    if data.get('status') == '1':
        pois = data.get('pois', [])
        print(f"\n✅ SUCCESS: Found {len(pois)} POIs")
        if pois:
            print(f"\n   First POI: {pois[0].get('name', 'N/A')}")
            print(f"   Location: {pois[0].get('location', 'N/A')}")
    else:
        print(f"\n❌ FAILED: {data.get('info', 'Unknown error')}")
        print(f"   Status code: {data.get('status')}")
        print(f"   Info code: {data.get('infocode')}")
    
except Exception as e:
    print(f"\n❌ EXCEPTION: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
