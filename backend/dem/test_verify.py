#!/usr/bin/env python3
"""Quick verification test for DEM + NDVI"""

import sys
from pathlib import Path

# Add parent directories to path
parent = Path(__file__).parent
sys.path.insert(0, str(parent.parent.parent))
sys.path.insert(0, str(parent.parent))

from dem.dem_service import DEMService
from dem.config import DEMConfig
from ndvi.ndvi_service import NDVIService
from ndvi.config import NDVIConfig
import logging

logging.basicConfig(level=logging.WARNING)

print('\n' + '='*70)
print('🔍 DEM + NDVI VERIFICATION TEST')
print('='*70)

dem = DEMService(
    DEMConfig.GEE_SERVICE_ACCOUNT_PATH,
    opentopo_api_key=DEMConfig.OPENTOPO_API_KEY,
    opentopo_api_url=DEMConfig.OPENTOPO_API_URL
)

ndvi = NDVIService(
    service_account_path=DEMConfig.GEE_SERVICE_ACCOUNT_PATH,
    nasa_api_key=NDVIConfig.NASA_API_KEY
)

# Test location: Beijing
lon, lat = 116.4074, 39.9042

print(f'\nTesting Beijing ({lon}, {lat})')
print('-'*70)

# Test 1: Elevation
print('\n[1] ELEVATION (OpenTopography)')
elev = dem.get_elevation(lon, lat)
if elev['success']:
    print(f'  ✓ {elev["elevation_m"]}m - {elev["source"]}')
else:
    print(f'  ✗ Failed: {elev.get("error")}')

# Test 2: Terrain Metrics
print('\n[2] TERRAIN METRICS')
terrain = dem.get_terrain_metrics(lon, lat)
if terrain['success']:
    print(f'  ✓ Slope: {terrain["slope_degrees"]:.2f}°')
    print(f'  ✓ Aspect: {terrain["aspect_degrees"]:.1f}° (0=N, 90=E, 180=S, 270=W)')
    print(f'  ✓ Ruggedness: {terrain["elevation_std"]:.2f}m')
else:
    print(f'  ✗ Failed: {terrain.get("error")}')

# Test 3: NDVI
print('\n[3] NDVI - VEGETATION INDEX (Sentinel-2)')
ndvi_result = ndvi.get_ndvi(lon, lat)
if ndvi_result['success']:
    print(f'  ✓ NDVI: {ndvi_result["ndvi_value"]:.3f}')
    print(f'  ✓ Category: {ndvi_result["ndvi_category"].upper()}')
    print(f'  ✓ Coverage: {ndvi_result["vegetation_coverage"]:.1%}')
else:
    print(f'  ✗ Failed: {ndvi_result.get("error")}')

# Test 4: Scores
print('\n[4] FENG SHUI SCORES')
topo = dem.get_topography_score(lon, lat)
veg = ndvi.get_vegetation_quality_score(lon, lat)

if topo['success'] and veg['success']:
    combined = (topo['topography_score'] + veg['vegetation_score']) / 2
    print(f'  ✓ Topography: {topo["topography_score"]:.1f}/100')
    print(f'  ✓ Vegetation: {veg["vegetation_score"]:.1f}/100')
    print(f'  ✓ COMBINED: {combined:.1f}/100')
    
    if combined >= 75:
        print('  → 🟢 EXCELLENT')
    elif combined >= 60:
        print('  → 🟡 GOOD')
    elif combined >= 45:
        print('  → 🟠 MODERATE')
    else:
        print('  → 🔴 POOR')
else:
    print(f'  ✗ Failed to calculate scores')

print('\n' + '='*70)
print('✓ VERIFICATION COMPLETE')
print('='*70 + '\n')
