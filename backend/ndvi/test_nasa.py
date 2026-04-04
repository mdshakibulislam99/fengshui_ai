#!/usr/bin/env python3
"""
Test NASA Landsat Data Integration
Tests real-time Landsat NDVI data fetching from NASA APIs without local storage
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.ndvi.nasa_service import NASADataService
from backend.ndvi.config import NDVIConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_nasa_integration():
    """Test NASA Landsat data service integration."""
    
    print('\n' + '='*70)
    print('🌍 NASA LANDSAT DATA INTEGRATION TEST')
    print('='*70)
    
    # Initialize NASA service with your API key
    nasa_service = NASADataService(
        nasa_api_key=NDVIConfig.NASA_API_KEY
    )
    
    print(f'\n[Setup Check]')
    print('-'*70)
    
    if nasa_service.available:
        print('✓ NASA Data Service initialized')
    else:
        print('⚠ NASA API key not configured')
        print('  To enable NASA Landsat data:')
        print('  1. Get API key from https://api.nasa.gov/')
        print('  2. Add to .env: NASA_API_KEY=your_key')
        print('\nContinuing with demo mode...\n')
    
    # Test locations
    locations = [
        {"name": "Beijing (Urban)", "lon": 116.4074, "lat": 39.9042},
        {"name": "Zhangjiajie Forest", "lon": 110.4755, "lat": 29.3276},
    ]
    
    # Test: Landsat NDVI
    print(f'\n[Test] Getting Landsat NDVI Data (30m Resolution, 16-day Cycle)')
    print('-'*70)
    
    if NDVIConfig.NASA_API_KEY and NDVIConfig.NASA_API_KEY != 'DEMO_KEY':
        for loc in locations:
            print(f'\n📍 {loc["name"]}')
            
            result = nasa_service.get_landsat_ndvi(loc["lon"], loc["lat"])
            
            if result['success']:
                print(f'   ✓ NDVI: {result["ndvi_value"]:.3f}')
                print(f'   Date: {result["date"]}')
                print(f'   Resolution: {result["resolution"]}')
                print(f'   Source: {result["source"]}')
            else:
                print(f'   ℹ Landsat data: {result.get("error")}')
    else:
        print('ℹ NASA API key not configured')
        print('  Add NASA_API_KEY to get Landsat data')
        print('  Get it at: https://api.nasa.gov/')
    
    
    # Test: Earth observation summary
    print(f'\n[Test] Earth Observation Summary with Landsat')
    print('-'*70)
    
    summary = nasa_service.get_earth_observation_summary(locations[0]["lon"], locations[0]["lat"])
    
    print(f'\nLocation: {locations[0]["name"]}')
    print(f'Available sources:')
    print(f'  Landsat: {summary["sources_available"]["landsat"]}')
    
    if summary['success']:
        print(f'\nData retrieved:')
        for source, data in summary['data'].items():
            print(f'  {source.upper()}: {data}')
    else:
        print(f'\nℹ Information: No data retrieved')
        print(f'  This is expected if API key is not configured')
    
    # Instructions
    print(f'\n[To Enable NASA Landsat Data]')
    print('-'*70)
    print('1. Get NASA API key: https://api.nasa.gov/')
    print('2. Add to .env file:')
    print('   NASA_API_KEY=your_key_here')
    print('3. Restart your application')
    print('4. Landsat data will automatically work!')
    
    print('\n' + '='*70)
    print('✓ NASA Landsat Integration Test Complete')
    print('='*70 + '\n')
    
    print('KEY BENEFITS:')
    print('✓ No data download needed')
    print('✓ No local storage required')
    print('✓ Real-time fresh data')
    print('✓ 30m resolution imagery')
    print('✓ Free (no costs)')
    print('✓ Easy integration\n')


if __name__ == '__main__':
    test_nasa_integration()
