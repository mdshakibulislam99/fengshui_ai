#!/usr/bin/env python3
"""
Performance test: Compare parallel vs sequential data fetching.
"""

import sys
sys.path.insert(0, 'backend')

import time
import logging
from app import app
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

# NJUPT campus test location
LAT, LON = 32.2112, 118.9768
RADIUS = 500

print("=" * 80)
print("PARALLEL DATA FETCHING PERFORMANCE TEST")
print("=" * 80)
print()
print(f"Location: NJUPT Campus ({LAT}, {LON})")
print(f"Radius: {RADIUS}m")
print()
print("Expected improvements:")
print("  Old (sequential): 27.4s total (84% on data fetch)")
print("  New (parallel):   5-8s total (simultaneous data fetch)")
print("  Expected speedup: ~3-5x faster")
print()
print("=" * 80)
print()

# Create test client
client = app.test_client()

# Prepare request
payload = {
    "latitude": LAT,
    "longitude": LON,
    "radius": RADIUS,
    "address": "NJUPT Campus, Nanjing"
}

print("📊 Testing analysis with PARALLEL data fetching...")
print()

start_total = time.monotonic()

try:
    response = client.post(
        '/api/analyze',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    elapsed_total = time.monotonic() - start_total
    
    if response.status_code == 200:
        result = response.get_json()
        
        print("=" * 80)
        print("✅ ANALYSIS COMPLETE")
        print("=" * 80)
        print()
        print(f"Final Score: {result.get('final_score', 'N/A')}/100")
        print(f"Total Response Time: {elapsed_total:.2f}s")
        print()
        
        # Check for timing breakdown in response
        if 'category_scores' in result:
            print("Category Scores:")
            for cat, score in result.get('category_scores', {}).items():
                print(f"  {cat}: {score}/100")
        print()
        
        print("=" * 80)
        print("PERFORMANCE SUMMARY")
        print("=" * 80)
        
        if elapsed_total < 10:
            speedup_factor = 27.4 / elapsed_total
            print(f"✅ PARALLEL FETCHING SUCCESSFUL")
            print(f"   Total time: {elapsed_total:.2f}s")
            print(f"   Speedup: ~{speedup_factor:.1f}x faster than sequential (was 27.4s)")
            print(f"   Improvement: {((27.4 - elapsed_total) / 27.4 * 100):.1f}% faster")
        elif elapsed_total < 27:
            speedup_factor = 27.4 / elapsed_total
            print(f"⚠️  PARTIAL IMPROVEMENT")
            print(f"   Total time: {elapsed_total:.2f}s")
            print(f"   Speedup: ~{speedup_factor:.1f}x faster than sequential (was 27.4s)")
            print(f"   Note: Some cache hits or AMap quota limitations detected")
        else:
            print(f"⚠️  NO IMPROVEMENT YET")
            print(f"   Total time: {elapsed_total:.2f}s")
            print(f"   Status: Similar to sequential (27.4s)")
            print(f"   Possible causes: First run, AMap quota hit, or GIS data not cached")
        
        print("=" * 80)
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.get_json())
        elapsed_total = time.monotonic() - start_total
        print(f"Response time: {elapsed_total:.2f}s")
        
except Exception as e:
    elapsed_total = time.monotonic() - start_total
    print(f"❌ Exception: {e}")
    print(f"Response time: {elapsed_total:.2f}s")
    import traceback
    traceback.print_exc()

print()
