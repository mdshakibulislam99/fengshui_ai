#!/usr/bin/env python3
"""
Test script to measure latency of feng shui analysis pipeline.
Tests individual services and the full pipeline.
"""

import sys
sys.path.insert(0, 'backend')

import time
import logging
from dem.dem_service import DEMService
from dem.config import DEMConfig
from ndvi.ndvi_service import NDVIService
from ndvi.config import NDVIConfig
from wind.cma_wind_service import CMAWindService
from wind.config import WindConfig
from Hydroshed.china_river_service import ChinaRiverService
from buildings_data.buildings_service import BuildingsService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Test location: NJUPT (Nanjing, China)
LAT, LON = 32.2112, 118.9768
RADIUS = 500

def test_service_latency(service_name, service_method, *args, **kwargs):
    """Measure latency of a single service call."""
    start = time.monotonic()
    try:
        result = service_method(*args, **kwargs)
        elapsed_ms = round((time.monotonic() - start) * 1000)
        success = result.get('success', False)
        status = "✓" if success else "✗"
        logger.info(f"{status} {service_name:20} {elapsed_ms:4}ms - {result.get('error', 'OK')}")
        return elapsed_ms, success
    except Exception as e:
        elapsed_ms = round((time.monotonic() - start) * 1000)
        logger.error(f"✗ {service_name:20} {elapsed_ms:4}ms - {str(e)[:50]}")
        return elapsed_ms, False

def main():
    logger.info("=" * 70)
    logger.info("FENG SHUI SYSTEM LATENCY TEST")
    logger.info("=" * 70)
    logger.info(f"Location: NJUPT (lat={LAT}, lon={LON}, radius={RADIUS}m)")
    logger.info("")
    
    # Initialize services
    logger.info("Initializing services...")
    dem_service = DEMService(
        service_account_path=None,
        opentopo_api_key=DEMConfig.OPENTOPO_API_KEY,
        opentopo_api_url=DEMConfig.OPENTOPO_API_URL
    )
    ndvi_service = NDVIService(service_account_path=None, nasa_api_key=None)
    wind_service = CMAWindService()
    river_service = ChinaRiverService()
    buildings_service = BuildingsService()
    logger.info("All services initialized")
    logger.info("")
    
    # Test each service individually
    logger.info("Testing individual service latencies:")
    logger.info("-" * 70)
    
    latencies = {}
    latencies['DEM'] = test_service_latency(
        'DEM/Topography',
        dem_service.get_topography_score,
        LON, LAT, RADIUS
    )
    
    latencies['NDVI'] = test_service_latency(
        'NDVI (MODIS)',
        ndvi_service.get_ndvi,
        LON, LAT, radius_m=RADIUS
    )
    
    latencies['Wind'] = test_service_latency(
        'Wind (CMA)',
        wind_service.get_wind_analysis,
        LON, LAT, RADIUS
    )
    
    latencies['River'] = test_service_latency(
        'River/Water',
        river_service.get_river_proximity_score,
        LON, LAT, RADIUS
    )
    
    latencies['Buildings'] = test_service_latency(
        'Buildings (3D)',
        buildings_service.get_building_data,
        LON, LAT, RADIUS
    )
    
    logger.info("")
    logger.info("-" * 70)
    logger.info("SUMMARY")
    logger.info("-" * 70)
    
    total_sequential = sum(lat[0] for lat in latencies.values())
    max_parallel = max(lat[0] for lat in latencies.values())
    
    logger.info(f"Sequential total:  {total_sequential:6}ms (if services run one-by-one)")
    logger.info(f"Parallel max:      {max_parallel:6}ms (services run in parallel)")
    logger.info(f"Expected savings:  {total_sequential - max_parallel:6}ms")
    logger.info("")
    logger.info("With feature extraction & scoring overhead (~1-2s), total should be:")
    logger.info(f"  ~{(max_parallel + 1500) // 1000}–{(max_parallel + 2500) // 1000} seconds (not 19+ seconds)")
    logger.info("")

if __name__ == '__main__':
    main()
