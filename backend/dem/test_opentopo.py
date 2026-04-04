#!/usr/bin/env python3
"""Quick test of OpenTopography integration"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.dem.config import DEMConfig
from backend.dem.dem_service import DEMService

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    print("="*70)
    print("🌍 Testing OpenTopography + GEE Fallback System")
    print("="*70)
    
    # Initialize service
    print("\nInitializing DEM service...")
    dem = DEMService(
        DEMConfig.GEE_SERVICE_ACCOUNT_PATH,
        opentopo_api_key=DEMConfig.OPENTOPO_API_KEY,
        opentopo_api_url=DEMConfig.OPENTOPO_API_URL
    )
    print("✓ Service initialized\n")
    
    # Test locations
    locations = [
        {"name": "Beijing", "lon": 116.4074, "lat": 39.9042},
        {"name": "Shanghai", "lon": 121.4737, "lat": 31.2304},
    ]
    
    for loc in locations:
        print(f"\n[{loc['name']}] ({loc['lon']}, {loc['lat']})")
        result = dem.get_elevation(loc['lon'], loc['lat'])
        
        if result['success']:
            print(f"  ✓ Elevation: {result['elevation_m']}m")
            print(f"  Source: {result['source']}")
            if result.get('used_fallback'):
                print(f"  💡 Used GEE fallback")
        else:
            print(f"  ✗ Failed: {result.get('error')}")
    
    print("\n" + "="*70)
    print("✓ Test complete!")
    print("="*70)

if __name__ == '__main__':
    main()
