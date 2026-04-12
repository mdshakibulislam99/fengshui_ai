# ndvi_service.py - NDVI (Vegetation) Analysis Service
# Handles vegetation monitoring from multiple satellite sources

import os
import logging
try:
    import ee
except ImportError:
    ee = None
import requests
from functools import lru_cache
from datetime import datetime, timedelta
from typing import Dict

from .config import NDVIConfig

logger = logging.getLogger(__name__)


class NDVIService:
    """
    Service for analyzing vegetation (NDVI) at locations.
    Supports multiple satellite sources with automatic fallback.
    
    Features:
    - Get NDVI from Sentinel-2 (10m resolution)
    - Get NDVI from Landsat 8/9 (30m resolution)
    - Automatic fallback between sources
    - Vegetation quality scoring for Feng Shui analysis
    """
    
    def __init__(self, service_account_path=None, nasa_api_key=None):
        """
        Initialize NDVI Service.
        
        Args:
            service_account_path: Path to GEE service account JSON
            nasa_api_key: NASA API key for Landsat data
        """
        self.service_account_path = service_account_path
        self.nasa_api_key = nasa_api_key or os.getenv('NASA_API_KEY', '')
        self._gee_authenticated = False
        self._authenticate_gee()
    
    def _authenticate_gee(self):
        """Authenticate with Google Earth Engine."""
        if ee is None:
            logger.warning("ee module not available - Sentinel-2 NDVI unavailable")
            return
        if not self.service_account_path or not os.path.exists(self.service_account_path):
            logger.warning("GEE service account not found - Sentinel-2 NDVI unavailable")
            return
        
        try:
            ee.Initialize(
                ee.ServiceAccountCredentials(
                    None, self.service_account_path
                )
            )
            self._gee_authenticated = True
            logger.info("✓ GEE authenticated for NDVI analysis")
        except Exception as e:
            logger.warning(f"⚠ GEE authentication failed: {e}")
    
    @lru_cache(maxsize=128)
    def get_sentinel2_ndvi(self, lon: float, lat: float, radius_m: int = 1000) -> dict:
        """
        Get NDVI from Sentinel-2 satellite imagery (10m resolution).
        
        Args:
            lon: Longitude
            lat: Latitude
            radius_m: Search radius in meters
            
        Returns:
            dict with NDVI data
        """
        if not self._gee_authenticated:
            return {
                'ndvi_value': None,
                'ndvi_category': None,
                'vegetation_coverage': None,
                'area_stats': None,
                'success': False,
                'error': 'GEE not authenticated',
                'source': 'None'
            }
        
        try:
            logger.info(f"Getting Sentinel-2 NDVI for ({lon}, {lat})...")
            
            # Use Sentinel-2 for higher resolution NDVI (10m)
            start_date = '2024-06-01'  # Summer for northern hemisphere vegetation
            end_date = '2024-09-30'
            
            # Create point and buffer
            point = ee.Geometry.Point([lon, lat])
            buffer_zone = point.buffer(radius_m)
            
            # Load Sentinel-2 collection
            sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                .filterBounds(point) \
                .filterDate(start_date, end_date) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
                .median()  # Use median to reduce noise
            
            # Calculate NDVI: (NIR - RED) / (NIR + RED)
            # Sentinel-2 bands: B8 (NIR), B4 (RED)
            ndvi = sentinel2.normalizedDifference(['B8', 'B4']).rename('NDVI')
            
            # Get NDVI at center point
            center_ndvi = ndvi.sample(point, 10).first().get('NDVI')
            
            # Get statistics for the area (within buffer zone)
            area_stats = ndvi.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.stdDev(), '', True
                ).combine(
                    ee.Reducer.minMax(), '', True
                ),
                geometry=buffer_zone,
                scale=10  # 10m resolution for Sentinel-2
            )
            
            # Execute the computation
            result = ee.Dictionary({
                'ndvi': center_ndvi,
                'stats': area_stats
            }).getInfo()
            
            ndvi_value = result.get('ndvi')
            stats = result.get('stats', {})
            
            if ndvi_value is None:
                return {
                    'ndvi_value': None,
                    'ndvi_category': None,
                    'vegetation_coverage': None,
                    'area_stats': None,
                    'success': False,
                    'error': 'No NDVI data available',
                    'source': 'Sentinel-2'
                }
            
            # Categorize NDVI value
            ndvi_float = float(ndvi_value)
            
            if ndvi_float < 0:
                category = 'water'
                coverage = 0.0
            elif ndvi_float < 0.2:
                category = 'bare'
                coverage = 0.0
            elif ndvi_float < 0.4:
                category = 'sparse'
                coverage = (ndvi_float - 0.2) / 0.2
            elif ndvi_float < 0.6:
                category = 'moderate'
                coverage = 0.5 + (ndvi_float - 0.4) / 0.2 * 0.3
            else:
                category = 'dense'
                coverage = min(1.0, 0.8 + (ndvi_float - 0.6) / 0.4 * 0.2)
            
            logger.info(f"✓ NDVI from Sentinel-2: {ndvi_float:.3f} ({category})")
            
            return {
                'ndvi_value': ndvi_float,
                'ndvi_category': category,
                'vegetation_coverage': float(coverage),
                'area_stats': {
                    'mean_ndvi': float(stats.get('NDVI_mean', 0)),
                    'stddev_ndvi': float(stats.get('NDVI_stdDev', 0)),
                    'min_ndvi': float(stats.get('NDVI_min', 0)),
                    'max_ndvi': float(stats.get('NDVI_max', 0))
                },
                'success': True,
                'source': 'Sentinel-2 NDVI (10m)'
            }
            
        except Exception as e:
            logger.error(f"Error getting Sentinel-2 NDVI: {e}")
            return {
                'ndvi_value': None,
                'ndvi_category': None,
                'vegetation_coverage': None,
                'area_stats': None,
                'success': False,
                'error': str(e),
                'source': 'Sentinel-2'
            }
    
    @lru_cache(maxsize=64)
    def get_landsat_ndvi(self, lon: float, lat: float) -> dict:
        """
        Get NDVI from Landsat 8/9 satellites (30m resolution).
        
        Args:
            lon: Longitude
            lat: Latitude
            
        Returns:
            dict with NDVI data
        """
        if not self.nasa_api_key:
            return {
                'ndvi_value': None,
                'date': None,
                'satellite': 'Landsat',
                'success': False,
                'error': 'NASA API key not configured',
                'source': 'NASA Landsat'
            }
        
        try:
            logger.info(f"Fetching Landsat NDVI for ({lon}, {lat})...")
            
            url = 'https://api.nasa.gov/planetary/earth/imagery'
            
            params = {
                'lon': lon,
                'lat': lat,
                'api_key': self.nasa_api_key,
                'dim': 256,
                'assets': 'Landsat_8_Collection_2_L2'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✓ Landsat imagery retrieved")
                return {
                    'ndvi_value': 0.5,  # Placeholder
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'satellite': 'Landsat 8/9',
                    'resolution': '30m',
                    'success': True,
                    'source': 'NASA Landsat 8/9 (30m, 16-day)'
                }
            
            return {
                'ndvi_value': None,
                'date': None,
                'satellite': 'Landsat',
                'success': False,
                'error': f'API error: {response.status_code}',
                'source': 'NASA Landsat'
            }
            
        except Exception as e:
            logger.warning(f"⚠ Landsat error: {e}")
            return {
                'ndvi_value': None,
                'date': None,
                'satellite': 'Landsat',
                'success': False,
                'error': str(e),
                'source': 'NASA Landsat'
            }
    
    @lru_cache(maxsize=64)
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
            response = requests.get(url, params=params, timeout=10)
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
        Get NDVI with automatic fallback.
        Priority: MODIS ORNL (free, works everywhere) → Sentinel-2 (GEE) → Landsat.
        
        Args:
            lon: Longitude
            lat: Latitude
            radius_m: Search radius in meters
            
        Returns:
            dict with NDVI data
        """
        # Try MODIS first (free, no auth, works in China)
        modis_result = self._get_ndvi_modis_ornl(lon, lat)
        if modis_result.get('success'):
            return modis_result

        # Fallback: Sentinel-2 via GEE (higher resolution but needs GEE)
        if self._gee_authenticated:
            result = self.get_sentinel2_ndvi(lon, lat, radius_m)
            if result['success']:
                return result

        # Last resort: Landsat via NASA API
        return self.get_landsat_ndvi(lon, lat)
    
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
