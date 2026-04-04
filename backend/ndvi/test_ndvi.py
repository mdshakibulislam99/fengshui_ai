#!/usr/bin/env python3
"""
Test NDVI Service
Tests vegetation analysis from multiple satellite sources
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.ndvi.ndvi_service import NDVIService
from backend.ndvi.config import NDVIConfig
from backend.dem.config import DEMConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ndvi():
    """Test NDVI service integration."""
    
    print('\n' + '='*70)
    print('🌿 NDVI (VEGETATION) SERVICE TEST')
    print('='*70)
    
    # Initialize NDVI service
    ndvi_service = NDVIService(
        service_account_path=DEMConfig.GEE_SERVICE_ACCOUNT_PATH,
        nasa_api_key=NDVIConfig.NASA_API_KEY
    )
    
    print(f'\n[Setup Check]')
    print('-'*70)
    print(f'✓ NDVI Service initialized')
    print(f'  GEE authenticated: {ndvi_service._gee_authenticated}')
    print(f'  NASA API available: {bool(NDVIConfig.NASA_API_KEY)}')
    
    # Test locations
    locations = [
        {"name": "Beijing (Urban)", "lon": 116.4074, "lat": 39.9042},
        {"name": "Shanghai (Urban)", "lon": 121.4737, "lat": 31.2304},
        {"name": "Zhangjiajie (Forest)", "lon": 110.4755, "lat": 29.3276},
    ]
    
    # Test 1: Sentinel-2 NDVI
    print(f'\n[Test 1] Sentinel-2 NDVI (10m Resolution)')
    print('-'*70)
    
    for loc in locations:
        print(f'\n📍 {loc["name"]}')
        result = ndvi_service.get_sentinel2_ndvi(loc["lon"], loc["lat"])
        
        if result['success']:
            print(f'   ✓ NDVI: {result["ndvi_value"]:.3f}')
            print(f'   Category: {result["ndvi_category"]}')
            print(f'   Coverage: {result["vegetation_coverage"]*100:.1f}%')
        else:
            print(f'   ℹ Error: {result.get("error")}')
    
    # Test 2: Vegetation Quality Score
    print(f'\n[Test 2] Feng Shui Vegetation Quality Score')
    print('-'*70)
    
    for loc in locations[:2]:  # Just first two to save time
        print(f'\n📍 {loc["name"]}')
        score_result = ndvi_service.get_vegetation_quality_score(
            loc["lon"], loc["lat"]
        )
        
        if score_result['success']:
            print(f'   Vegetation Score: {score_result["vegetation_score"]:.1f}/100')
            print(f'   - NDVI Component: {score_result["ndvi_component"]:.1f}')
            print(f'   - Coverage Component: {score_result["coverage_component"]:.1f}')
            print(f'   - Uniformity Component: {score_result["uniformity_component"]:.1f}')
        else:
            print(f'   ℹ Error: {score_result.get("error")}')
    
    # Test 3: Multi-source NDVI (auto fallback)
    print(f'\n[Test 3] NDVI with Automatic Fallback')
    print('-'*70)
    
    loc = locations[0]
    print(f'\n📍 {loc["name"]}')
    print('Trying: Sentinel-2 → Landsat')
    
    result = ndvi_service.get_ndvi(loc["lon"], loc["lat"])
    
    if result['success']:
        print(f'   ✓ Got NDVI: {result["ndvi_value"]:.3f}')
        print(f'   Source: {result.get("source", "Unknown")}')
    else:
        print(f'   ℹ Error: {result.get("error")}')
    
    # Summary
    print(f'\n[Summary]')
    print('-'*70)
    print('✓ NDVI Service provides vegetation analysis from:')
    print('  1. Sentinel-2 (10m resolution, primary)')
    print('  2. Landsat 8/9 (30m resolution, fallback)')
    print('✓ Automatic fallback ensures data availability')
    print('✓ Feng Shui vegetation scoring integrated')
    
    print('\n' + '='*70)
    print('✓ NDVI Test Complete')
    print('='*70 + '\n')


if __name__ == '__main__':
    test_ndvi()
