# Test script for GEE Flood Risk Service

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flood_service import GEEFloodService
from config import flood_config

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_flood_service():
    print("\n🌊 Starting GEE Flood Service Tests...\n")

    service = GEEFloodService(flood_config.GEE_SERVICE_ACCOUNT_PATH)

    if not service.enabled:
        print("⚠️ Flood service is disabled in config")
        return

    print(f"✓ Flood service initialized")
    print(f"  Service enabled: {service.enabled}")
    print(f"  GEE authenticated: {service._authenticated}")

    test_locations = [
        (39.9042, 116.4074, "Beijing"),
        (31.2304, 121.4737, "Shanghai"),
        (23.1291, 113.2644, "Guangzhou"),
    ]

    for lat, lon, name in test_locations:
        print("\n" + "=" * 80)
        print(f"📍 {name} ({lat:.4f}, {lon:.4f})")
        print("=" * 80)

        result = service.get_flood_risk_analysis(lon, lat, 500)

        if result['success']:
            scores = result['flood_scores']
            metrics = result['flood_metrics']

            print("\n✅ FLOOD SCORES")
            print(f"  Flood Risk Index: {scores['flood_risk_index']}/100")
            print(f"  Flood Exposure: {scores['flood_exposure_score']}/100")
            print(f"  Flood Level: {scores['flood_level']}")

            print("\n📊 FLOOD METRICS")
            print(f"  Distance to persistent water: {metrics['distance_to_persistent_water_m']:.1f} m")
            print(f"  Surface water occurrence: {metrics['surface_water_occurrence_pct']:.2f}%")
            print(f"  Surface water seasonality: {metrics['surface_water_seasonality_months']:.2f} months")
            print(f"  Mean slope: {metrics['mean_slope_degrees']:.2f}°")
            print(f"  Rainfall p95: {metrics['rainfall_p95_mm_day']:.2f} mm/day")
            print(f"  Heavy rain frequency: {metrics['heavy_rain_frequency']:.3f}")
        else:
            print(f"❌ Analysis failed: {result['error']}")

    print("\n" + "=" * 80)
    print("✅ Flood tests completed")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    test_flood_service()
