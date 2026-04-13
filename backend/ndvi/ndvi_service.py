# ndvi_service.py - NDVI (Vegetation) Analysis Service
# Uses MODIS satellite data (free, China-accessible) - no GEE or NASA API

import os
import logging
import requests
from functools import lru_cache
from datetime import datetime, timedelta
from typing import Dict

from .config import NDVIConfig

logger = logging.getLogger(__name__)


class NDVIService:
    """
    Service for analyzing vegetation (NDVI) at locations.
    Uses MODIS satellite data (free, China-accessible).
    No GEE or NASA API dependency.
    
    Features:
    - Get NDVI from MODIS MOD13Q1 250m resolution (ORNL DAAC)
    - Fast response times (~1-2 seconds)
    - Free access, no authentication required
    - Works reliably across China
    """
    
    def __init__(self, service_account_path=None, nasa_api_key=None):
        """
        Initialize NDVI Service.
        
        Args:
            service_account_path: Deprecated - not used (GEE removed)
            nasa_api_key: Deprecated - not used (NASA removed)
        """
        # GEE and NASA removed - MODIS is primary source
        logger.info("✓ NDVI service initialized (MODIS MOD13Q1 250m - free, no auth required)")
    
    @lru_cache(maxsize=512)  # Increased from 64 to handle more unique locations
    def _get_ndvi_modis_ornl(self, lon: float, lat: float) -> dict:
        """
        Get NDVI from MODIS MOD13A1 via ORNL DAAC REST API.
        Completely free, no API key or authentication required.
        Returns real 500m-resolution NDVI values, 16-day composites.
        https://modis.ornl.gov/rst/ui/
        """
        try:
            # Use peak-summer of last full year — only 2 MODIS composites (fast response)
            year = datetime.now().year - 1
            # DOY 161 = Jun 9, DOY 177 = Jun 25 → 2 peak-green composites
            url = 'https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset'
            params = {
                'latitude': lat,
                'longitude': lon,
                'startDate': f'A{year}161',
                'endDate': f'A{year}177',
                'kmAboveBelow': 0,
                'kmLeftRight': 0,
            }
            # Reduced timeout from 10s to 5s to fail fast if ORNL is slow
            response = requests.get(url, params=params, timeout=5)
            if response.status_code != 200:
                logger.warning(f"⚠ MODIS ORNL API error: {response.status_code}")
                return {'success': False, 'error': f'MODIS ORNL API {response.status_code}'}

            data = response.json()
            subsets = data.get('subset', [])

            ndvi_values = []
            for subset in subsets:
                if subset.get('band') == '250m_16_days_NDVI':
                    # scale is 0.0001 per MODIS MOD13Q1 specification
                    raw_scale = subset.get('scale')
                    scale = float(raw_scale) if raw_scale is not None else 0.0001
                    fill_value = int(subset.get('fill_value', -3000))
                    for raw in subset.get('data', []):
                        if raw != fill_value and raw > -2000:
                            ndvi_val = raw * scale
                            if -1.0 <= ndvi_val <= 1.0:
                                ndvi_values.append(ndvi_val)

            if not ndvi_values:
                return {'success': False, 'error': 'No valid MODIS NDVI pixels at location'}

            ndvi = float(sum(ndvi_values) / len(ndvi_values))

            if ndvi < 0:
                category, coverage = 'water', 0.0
            elif ndvi < 0.2:
                category, coverage = 'bare', 0.0
            elif ndvi < 0.4:
                category, coverage = 'sparse', (ndvi - 0.2) / 0.2
            elif ndvi < 0.6:
                category, coverage = 'moderate', 0.5 + (ndvi - 0.4) / 0.2 * 0.3
            else:
                category, coverage = 'dense', min(1.0, 0.8 + (ndvi - 0.6) / 0.4 * 0.2)

            logger.info(f"✓ NDVI from MODIS ORNL: {ndvi:.3f} ({category})")
            return {
                'ndvi_value': ndvi,
                'ndvi_category': category,
                'vegetation_coverage': float(coverage),
                'area_stats': {
                    'mean_ndvi': ndvi,
                    'stddev_ndvi': 0.05,  # single-pixel, no spatial variance
                    'min_ndvi': float(min(ndvi_values)),
                    'max_ndvi': float(max(ndvi_values)),
                },
                'success': True,
                'source': 'MODIS MOD13Q1 250m (free, ORNL DAAC)'
            }
        except Exception as e:
            logger.warning(f"⚠ MODIS ORNL error: {e}")
            return {'success': False, 'error': str(e)}

    def get_ndvi(self, lon: float, lat: float, radius_m: int = 1000) -> dict:
        """
        Get NDVI using MODIS (free, China-accessible).
        
        Args:
            lon: Longitude
            lat: Latitude
            radius_m: Search radius in meters
            
        Returns:
            dict with NDVI data
        """
        # Use MODIS ORNL (free, no auth, works everywhere in China, fast ~1-2s)
        return self._get_ndvi_modis_ornl(lon, lat)
    
    def get_vegetation_quality_score(self, lon: float, lat: float, radius_m: int = 1000) -> dict:
        """
        Convert NDVI into Feng Shui vegetation quality score (0-100).
        
        Args:
            lon: Longitude
            lat: Latitude
            radius_m: Search radius for vegetation analysis
            
        Returns:
            dict with vegetation quality score
        """
        ndvi_result = self.get_ndvi(lon, lat, radius_m)
        
        if not ndvi_result['success']:
            return {
                'vegetation_score': 0,
                'ndvi_component': 0,
                'coverage_component': 0,
                'uniformity_component': 0,
                'ndvi_data': ndvi_result,
                'success': False
            }
        
        # NDVI-based score
        ndvi = ndvi_result['ndvi_value']
        if ndvi >= 0.6:
            ndvi_score = 100
        elif ndvi >= 0.4:
            ndvi_score = 75 + (ndvi - 0.4) / 0.2 * 25
        elif ndvi >= 0.2:
            ndvi_score = 50 + (ndvi - 0.2) / 0.2 * 25
        elif ndvi > 0:
            ndvi_score = 25 + ndvi / 0.2 * 25
        else:
            ndvi_score = max(0, 25 + ndvi * 25)
        
        # Coverage score
        coverage = ndvi_result.get('vegetation_coverage', 0)
        coverage_score = coverage * 100
        
        # Uniformity score
        stats = ndvi_result.get('area_stats', {})
        stddev = stats.get('stddev_ndvi', 0) if stats else 0
        
        if stddev <= 0.1:
            uniformity_score = 100
        elif stddev <= 0.2:
            uniformity_score = 80
        elif stddev <= 0.3:
            uniformity_score = 60
        else:
            uniformity_score = max(20, 100 - stddev * 200)
        
        # Combine with Feng Shui weights
        vegetation_score = (
            ndvi_score * 0.40 +
            coverage_score * 0.35 +
            uniformity_score * 0.25
        )
        
        return {
            'vegetation_score': float(vegetation_score),
            'ndvi_component': float(ndvi_score),
            'coverage_component': float(coverage_score),
            'uniformity_component': float(uniformity_score),
            'ndvi_data': ndvi_result,
            'success': True
        }
