#!/usr/bin/env python3
"""
Test script for DEM (Digital Elevation Model) integration with Google Earth Engine.
Tests elevation and terrain data retrieval for Feng Shui analysis.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dem import DEMService
from dem.config import DEMConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dem_integration():
    """Test DEM service initialization and functionality."""
    
    print("\n" + "=" * 70)
    print("🌍 DEM (Google Earth Engine) Integration Test")
    print("=" * 70)
    
    # Test 1: Initialize DEM Service
    print("\n[Test 1] Initializing DEM Service...")
    print(f"  Service Account: {DEMConfig.GEE_SERVICE_ACCOUNT_PATH}")
    print(f"  OpenTopography API: {DEMConfig.OPENTOPO_API_KEY[:10]}...")
    
    try:
        dem_service = DEMService(
            DEMConfig.GEE_SERVICE_ACCOUNT_PATH,
            opentopo_api_key=DEMConfig.OPENTOPO_API_KEY,
            opentopo_api_url=DEMConfig.OPENTOPO_API_URL
        )
        print("  ✓ DEM service initialized successfully (OpenTopography + GEE fallback)!")
    except Exception as e:
        print(f"  ✗ Failed to initialize DEM service: {e}")
        return False
    
    # Test 2: Get elevation at specific locations
    print("\n[Test 2] Testing elevation data retrieval...")
    test_locations = [
        {"name": "Beijing Center", "lon": 116.4074, "lat": 39.9042},
        {"name": "Shanghai Center", "lon": 121.4737, "lat": 31.2304},
        {"name": "Shenzhen Center", "lon": 114.0579, "lat": 22.5431},
    ]
    
    for location in test_locations:
        print(f"\n  Location: {location['name']} ({location['lon']}, {location['lat']})")
        result = dem_service.get_elevation(location['lon'], location['lat'])
        
        if result['success']:
            print(f"    ✓ Elevation: {result['elevation_m']:.1f} m")
        else:
            print(f"    ✗ Failed: {result.get('error', 'Unknown error')}")
    
    # Test 3: Get comprehensive terrain metrics
    print("\n[Test 3] Testing terrain metrics retrieval...")
    print(f"  Location: Beijing Center (search radius: 500m)")
    
    metrics = dem_service.get_terrain_metrics(116.4074, 39.9042, radius_m=500)
    
    if metrics['success']:
        print(f"    ✓ Elevation: {metrics['elevation_m']:.1f} m")
        print(f"    ✓ Slope: {metrics['slope_degrees']:.2f}°")
        print(f"    ✓ Aspect: {metrics['aspect_degrees']:.1f}° (0=N, 90=E, 180=S, 270=W)")
        print(f"    ✓ Elevation Std Dev: {metrics['elevation_std']:.1f} m (ruggedness)")
    else:
        print(f"    ✗ Failed: {metrics.get('error', 'Unknown error')}")
    
    # Test 4: Get Feng Shui topography score
    print("\n[Test 4] Testing Feng Shui topography score...")
    
    topography = dem_service.get_topography_score(116.4074, 39.9042, radius_m=500)
    
    if topography['success']:
        print(f"    ✓ Overall Topography Score: {topography['topography_score']:.1f}/100")
        print(f"      - Elevation contribution: {topography['elevation_contribution']:.1f}")
        print(f"      - Slope contribution: {topography['slope_contribution']:.1f}")
        print(f"      - Aspect contribution: {topography['aspect_contribution']:.1f}")
        print(f"      - Ruggedness contribution: {topography['ruggedness_contribution']:.1f}")
    else:
        print(f"    ✗ Failed: {topography.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 70)
    print("✓ All DEM integration tests completed!")
    print("=" * 70 + "\n")
    
    return True

if __name__ == '__main__':
    success = test_dem_integration()
    sys.exit(0 if success else 1)
