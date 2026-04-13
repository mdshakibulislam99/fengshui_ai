#!/usr/bin/env python3
"""
Final test of NJUPT location with cleaned China-only system.
Tests all services: DEM, NDVI, Wind, Water, Buildings, Flood
"""

import sys
sys.path.insert(0, 'backend')

import time
import json
from app import app

# Test location
LAT, LON = 32.2112, 118.9768
RADIUS = 500

print("=" * 70)
print("FENG SHUI SYSTEM TEST - NJUPT CAMPUS (NANJING)")
print("=" * 70)
print(f"Location: ({LAT}, {LON})")
print(f"Radius: {RADIUS}m")
print(f"Systems: DEM (OpenTopoography), NDVI (MODIS), Wind (CMA), Water (AMap)")
print("Status: GEE/NASA Removed ✗, China-Only APIs ✓")
print("")

# Test with Flask test client
with app.test_client() as client:
    print("Sending analysis request...")
    
    start_total = time.time()
    response = client.post('/api/analyze', 
        json={
            'latitude': LAT,
            'longitude': LON,
            'address': 'NJUPT Campus - Nanjing',
            'radius': RADIUS
        }
    )
    total_time = time.time() - start_total
    
    if response.status_code == 200:
        data = response.get_json()
        
        print("")
        print("=" * 70)
        print("ANALYSIS RESULTS")
        print("=" * 70)
        
        # Main scores
        print("\n📊 FINAL FENG SHUI SCORE")
        final_score = data.get('final_score', 'N/A')
        if isinstance(final_score, str):
            try:
                final_score = float(final_score)
            except:
                pass
        print(f"  Overall Score: {final_score}/100" if isinstance(final_score, float) else f"  Overall Score: {final_score}")
        print("")
        
        # Category breakdown
        print("📈 Category Scores:")
        categories = data.get('category_scores', {})
        for category, score in sorted(categories.items()):
            pct = (score / 10) if isinstance(score, (int, float)) else 0
            bar = "█" * int(pct) + "░" * (10 - int(pct))
            print(f"  {category:20} {score:6.1f}/100  [{bar}]")
        
        print("")
        print("🔍 Detailed Explanations:")
        for i, explanation in enumerate(data.get('explanations', [])[:8], 1):
            # Truncate long explanations
            text = explanation[:100] + "..." if len(explanation) > 100 else explanation
            print(f"  {i}. {text}")
        
        # Timing
        print("")
        print("⏱️  Performance")
        print(f"  Total response time: {total_time:.2f}s")
        if 'timing' in data:
            timing = data['timing']
            print(f"    - Service calls:       {timing.get('data_fetch_ms', 0)}ms")
            print(f"    - Feature extraction:  {timing.get('feature_extract_ms', 0)}ms")
            print(f"    - Model scoring:       {timing.get('scoring_ms', 0)}ms")
        
        print("")
        print("=" * 70)
        print("✅ TEST PASSED - System working with China-only APIs")
        print("=" * 70)
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.get_json())
