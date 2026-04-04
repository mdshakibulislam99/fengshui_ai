#!/usr/bin/env python3
"""
Test HydroSHEDS integration using Google Earth Engine.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.Hydroshed.hydrosheds_service import HydroSHEDSService
from backend.Hydroshed.config import HydroSHEDSConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_hydrosheds():
    print('\n' + '=' * 70)
    print('🌊 HYDROSHEDS (RIVER) SERVICE TEST')
    print('=' * 70)

    service = HydroSHEDSService(HydroSHEDSConfig.HYDROSHEDS_GEE_SERVICE_ACCOUNT_PATH)

    print('\n[Setup Check]')
    print('-' * 70)
    print(f'✓ Service initialized')
    print(f'  Enabled: {HydroSHEDSConfig.HYDROSHEDS_ENABLE}')
    print(f'  GEE authenticated: {service._authenticated}')
    print(f'  Dataset: {HydroSHEDSConfig.HYDROSHEDS_FLOW_ACC_DATASET}')
    print(f'  Threshold: {HydroSHEDSConfig.HYDROSHEDS_FLOW_ACC_THRESHOLD}')

    locations = [
        {"name": "Beijing", "lon": 116.4074, "lat": 39.9042},
        {"name": "Shanghai", "lon": 121.4737, "lat": 31.2304},
        {"name": "Guangzhou", "lon": 113.2644, "lat": 23.1291},
    ]

    print('\n[Test 1] River metrics from HydroSHEDS')
    print('-' * 70)
    for loc in locations:
        result = service.get_river_metrics(loc['lon'], loc['lat'], radius_m=1000)
        print(f"\n📍 {loc['name']}")
        if result['success']:
            print(f"   ✓ Distance to river: {result['river_distance_m']:.1f} m")
            print(f"   ✓ River density: {result['river_density']:.3f}")
            print(f"   ✓ Flow accumulation: {result['flow_acc_value']:.1f}")
        else:
            print(f"   ℹ Error: {result.get('error', 'Unknown error')}")

    print('\n[Test 2] River proximity score for Feng Shui')
    print('-' * 70)
    sample = locations[0]
    score = service.get_river_proximity_score(sample['lon'], sample['lat'], radius_m=1000)
    print(f"\n📍 {sample['name']}")
    print(f"   Combined River Score: {score['combined_score']:.1f}/100")
    print(f"   Distance Score: {score['river_proximity_score']:.1f}/100")
    print(f"   Density Score: {score['river_density_score']:.1f}/100")
    print(f"   Source: {score.get('source', 'HydroSHEDS')}")

    print('\n' + '=' * 70)
    print('✓ HydroSHEDS Test Complete')
    print('=' * 70 + '\n')


if __name__ == '__main__':
    test_hydrosheds()
