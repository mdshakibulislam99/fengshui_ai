# dem_service.py - DEM Service with OpenTopography (Primary) and Open-Elevation (Free Fallback)
# Uses only China-accessible services - no GEE dependency

import os
import json
import logging
import math
import numpy as np
from pathlib import Path
import requests
from functools import lru_cache

logger = logging.getLogger(__name__)

class DEMService:
    """
    Service for accessing elevation and terrain data.
    Uses OpenTopography as primary source, with Open-Elevation as free fallback.
    No Google Earth Engine dependency.
    """
    
    def __init__(self, service_account_path=None, opentopo_api_key=None, opentopo_api_url=None):
        """
        Initialize DEM service with OpenTopography (China-accessible).
        
        Args:
            service_account_path: Deprecated - not used (kept for compatibility)
            opentopo_api_key: OpenTopography API key (optional)
            opentopo_api_url: OpenTopography API endpoint (optional)
        """
        self.opentopo_api_key = opentopo_api_key
        self.opentopo_api_url = opentopo_api_url or 'https://portal.opentopography.org/API/globaldem'
        self.opentopo_dem_type = 'SRTMGL1'  # SRTM 30m resolution
        self._opentopo_available = bool(opentopo_api_key)
        
        logger.info("✓ DEM service initialized (OpenTopography + Open-Elevation free fallback - no GEE needed)")
    
    def _get_elevation_opentopo(self, lon: float, lat: float) -> dict:
        """
        Get elevation from OpenTopography API.
        
        Args:
            lon: Longitude
            lat: Latitude
            
        Returns:
            dict with elevation data or error
        """
        if not self._opentopo_available:
            return {'success': False, 'error': 'OpenTopography not configured'}
        
        try:
            # OpenTopography Global DEM API parameters
            # Create a small bounding box around the point
            # Use 0.01 degrees (~1km at equator) as OpenTopography requires minimum area
            buffer = 0.01
            params = {
                'demtype': self.opentopo_dem_type,
                'south': lat - buffer,
                'north': lat + buffer,
                'west': lon - buffer,
                'east': lon + buffer,
                'outputFormat': 'AAIGrid',  # ASCII Grid format for easy parsing
                'API_Key': self.opentopo_api_key
            }
            
            logger.debug(f"OpenTopography request params: {params}")
            response = requests.get(self.opentopo_api_url, params=params, timeout=5)
            
            # Check for rate limiting or quota exceeded
            if response.status_code == 429:
                logger.warning("⚠ OpenTopography rate limit exceeded")
                return {'success': False, 'error': 'Rate limit exceeded', 'rate_limited': True}
            
            if response.status_code == 403:
                logger.warning("⚠ OpenTopography daily quota exceeded")
                return {'success': False, 'error': 'Daily quota exceeded', 'quota_exceeded': True}
            
            if response.status_code != 200:
                logger.warning(f"⚠ OpenTopography API error: {response.status_code} - {response.text[:200]}")
                return {'success': False, 'error': f'API error: {response.status_code}'}
            
            # Parse AAIGrid format (ASCII grid)
            # Format:
            # ncols         3
            # nrows         3
            # xllcorner     116.4073
            # yllcorner     39.9041
            # cellsize      0.000083333333333
            # NODATA_value  -9999
            # 54 55 54
            # 53 54 55
            # 54 54 53
            
            lines = response.text.strip().split('\n')
            elevation_values = []
            
            # Skip header lines and parse elevation data
            data_started = False
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Skip header lines
                if any(keyword in line.lower() for keyword in ['ncols', 'nrows', 'xllcorner', 'yllcorner', 'cellsize', 'nodata']):
                    continue
                
                # Parse elevation values
                try:
                    row_values = [float(v) for v in line.split() if v != '-9999']
                    elevation_values.extend(row_values)
                except ValueError:
                    continue
            
            if elevation_values:
                # Use median elevation from the small grid
                elevation = sorted(elevation_values)[len(elevation_values) // 2]
                logger.info(f"✓ Elevation from OpenTopography: {elevation}m")
                return {
                    'elevation_m': elevation,
                    'success': True,
                    'source': 'OpenTopography SRTM 30m'
                }
            
            return {'success': False, 'error': 'Could not parse elevation data'}
            
        except requests.exceptions.Timeout:
            logger.warning("⚠ OpenTopography request timeout")
            return {'success': False, 'error': 'Request timeout'}
        except Exception as e:
            logger.warning(f"⚠ OpenTopography error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_elevation_open_elevation(self, lat: float, lon: float) -> dict:
        """
        Get elevation from Open-Elevation API (free, no API key required).
        Uses SRTM 30m data globally. https://open-elevation.com
        """
        try:
            url = 'https://api.open-elevation.com/api/v1/lookup'
            response = requests.post(
                url,
                json={'locations': [{'latitude': lat, 'longitude': lon}]},
                timeout=5
            )
            if response.status_code == 200:
                results = response.json().get('results', [])
                if results and results[0].get('elevation') is not None:
                    elevation = float(results[0]['elevation'])
                    logger.info(f"✓ Elevation from Open-Elevation: {elevation}m")
                    return {
                        'elevation_m': elevation,
                        'success': True,
                        'source': 'Open-Elevation SRTM 30m (free)'
                    }
            return {'success': False, 'error': f'Open-Elevation API returned {response.status_code}'}
        except Exception as e:
            logger.warning(f"⚠ Open-Elevation error: {e}")
            return {'success': False, 'error': str(e)}

    def _get_terrain_metrics_open_elevation(self, lat: float, lon: float, radius_m: int = 500) -> dict:
        """
        Compute terrain metrics (slope, aspect, ruggedness) from a 3x3 grid of
        Open-Elevation samples. No API key required.
        """
        try:
            # Convert radius to degrees
            lat_rad = math.radians(lat)
            dlat = (radius_m / 2) / 111320
            dlon = (radius_m / 2) / (111320 * math.cos(lat_rad))
            step_m = radius_m / 2  # metres between grid points

            locations = [
                {'latitude': lat + dy * dlat, 'longitude': lon + dx * dlon}
                for dy in [-1, 0, 1]
                for dx in [-1, 0, 1]
            ]

            url = 'https://api.open-elevation.com/api/v1/lookup'
            response = requests.post(url, json={'locations': locations}, timeout=5)
            if response.status_code != 200:
                return {'success': False, 'error': f'Open-Elevation error {response.status_code}'}

            results = response.json().get('results', [])
            if len(results) < 9:
                return {'success': False, 'error': 'Insufficient elevation grid data'}

            elev_grid = np.array(
                [r.get('elevation', 0) for r in results], dtype=float
            ).reshape(3, 3)

            center_elevation = float(elev_grid[1, 1])
            elevation_std = float(np.std(elev_grid))

            # Gradient in m/m (elevation change per metre of horizontal distance)
            gy, gx = np.gradient(elev_grid, step_m, step_m)
            cx, cy = float(gx[1, 1]), float(gy[1, 1])

            slope_rad = math.atan(math.sqrt(cx ** 2 + cy ** 2))
            slope_degrees = math.degrees(slope_rad)

            # Aspect: 0=N, 90=E, 180=S, 270=W
            aspect_degrees = (math.degrees(math.atan2(cx, -cy)) + 360) % 360

            logger.info(
                f"✓ Terrain metrics from Open-Elevation: elev={center_elevation}m "
                f"slope={slope_degrees:.1f}° aspect={aspect_degrees:.1f}°"
            )
            return {
                'elevation_m': center_elevation,
                'slope_degrees': slope_degrees,
                'aspect_degrees': aspect_degrees,
                'elevation_std': elevation_std,
                'success': True,
                'source': 'Open-Elevation SRTM 30m - terrain grid (free)'
            }
        except Exception as e:
            logger.warning(f"⚠ Open-Elevation terrain metrics error: {e}")
            return {'success': False, 'error': str(e)}

    @lru_cache(maxsize=128)
    def get_elevation(self, lon: float, lat: float) -> dict:
        """
        Get elevation at a specific point.
        Tries OpenTopography first, falls back to Google Earth Engine if it fails.
        
        Args:
            lon: Longitude
            lat: Latitude
            
        Returns:
            dict with elevation data:
            {
                'elevation_m': float,
                'success': bool,
                'source': str,
                'used_fallback': bool (optional)
            }
        """
        # Try OpenTopography first
        if self._opentopo_available:
            logger.info(f"Attempting OpenTopography for ({lon}, {lat})...")
            result = self._get_elevation_opentopo(lon, lat)
            
            if result.get('success'):
                return result
            
            # Log why OpenTopography failed
            error = result.get('error', 'Unknown error')
            logger.warning(f"OpenTopography failed: {error}. Falling back to GEE...")
        
        # Fallback to Open-Elevation (free, no key required)
        logger.info(f"Trying Open-Elevation free API for ({lon}, {lat})...")
        oe_result = self._get_elevation_open_elevation(lat, lon)
        if oe_result.get('success'):
            return oe_result

        # All DEM sources exhausted - return error
        logger.error("All DEM sources exhausted (OpenTopography, Open-Elevation fallback)")
        return {
            'elevation_m': None,
            'success': False,
            'source': 'None',
            'error': 'No DEM sources available'
        }
    
    @lru_cache(maxsize=128)
    def get_terrain_metrics(self, lon: float, lat: float, radius_m: int = 500) -> dict:
        """
        Get comprehensive terrain metrics for Feng Shui analysis.
        Uses GEE for terrain analysis (slope, aspect, ruggedness) as it has built-in terrain processing.
        For elevation only, use get_elevation() which tries OpenTopography first.
        
        Args:
            lon: Longitude
            lat: Latitude
            radius_m: Search radius in meters
            
        Returns:
            dict with terrain metrics:
            {
                'elevation_m': float,
                'slope_degrees': float,
                'aspect_degrees': float,  # 0=N, 90=E, 180=S, 270=W
                'elevation_std': float,   # Local terrain ruggedness
                'success': bool,
                'source': str
            }
        """
        # Use Open-Elevation as fallback (GEE removed)
        logger.info(f"Using Open-Elevation grid for terrain metrics at ({lon}, {lat})")
        return self._get_terrain_metrics_open_elevation(lat, lon, radius_m)
    
    @lru_cache(maxsize=128)
    def get_topography_score(self, lon: float, lat: float, radius_m: int = 500) -> dict:
        """
        Convert terrain metrics to Feng Shui topography score (0-100).
        
        Args:
            lon: Longitude
            lat: Latitude
            radius_m: Search radius for terrain analysis
            
        Returns:
            dict with topography score and component breakdown:
            {
                'topography_score': float (0-100),
                'elevation_contribution': float,
                'slope_contribution': float,
                'aspect_contribution': float,
                'ruggedness_contribution': float,
                'terrain_metrics': dict,
                'success': bool
            }
        """
        metrics = self.get_terrain_metrics(lon, lat, radius_m)
        
        if not metrics['success']:
            return {
                'topography_score': 0,
                'elevation_contribution': 0,
                'slope_contribution': 0,
                'aspect_contribution': 0,
                'ruggedness_contribution': 0,
                'terrain_metrics': metrics,
                'success': False
            }
        
        # Normalize and score each component
        
        # Elevation: Optimal 100-300m (not too high, not too low)
        elev = metrics.get('elevation_m') or 0
        if 100 <= elev <= 300:
            elev_score = 100
        elif elev < 100:
            elev_score = max(0, 50 + (elev / 2))  # Increases from 50 to 100 as elev goes 0->100
        else:  # elev > 300
            elev_score = max(0, 100 - ((elev - 300) / 100))  # Decreases as elevation increases
        
        # Slope: Optimal 5-30 degrees (not too steep, not too flat)
        slope = metrics.get('slope_degrees') or 0
        if 5 <= slope <= 30:
            slope_score = 100 - ((slope - 5) / 25) * 20  # Slight preference for gentler slopes
        elif slope < 5:
            slope_score = max(0, 100 - ((5 - slope) * 10))  # Too flat is bad
        else:  # slope > 30
            slope_score = max(0, 100 - ((slope - 30) / 10) * 30)  # Too steep is bad
        
        # Aspect: All directions good, but S/SE/E better for solar exposure
        aspect = metrics.get('aspect_degrees') or 0
        # South = 180, East = 90, North = 0, West = 270
        if 135 <= aspect <= 225:  # SE to SW (S-facing)
            aspect_score = 100
        elif 45 <= aspect < 135 or 225 < aspect <= 315:  # E-facing or W-facing
            aspect_score = 80
        else:  # N-facing
            aspect_score = 60
        
        # Ruggedness: Moderate variation is good (not flat, not too chaotic)
        elev_std = metrics.get('elevation_std') or 0
        if 10 <= elev_std <= 50:
            ruggedness_score = 100
        elif elev_std < 10:
            ruggedness_score = max(0, 50 + (elev_std / 10) * 50)  # Too flat is less ideal
        else:
            ruggedness_score = max(0, 100 - ((elev_std - 50) / 100) * 50)  # Too chaotic is bad
        
        # Combine scores with Feng Shui weights
        topography_score = (
            elev_score * 0.30 +      # Elevation is important for grounding
            slope_score * 0.25 +     # Slope affects energy flow
            aspect_score * 0.25 +    # Aspect affects light/warmth
            ruggedness_score * 0.20  # Variation indicates good dragon veins
        )
        
        return {
            'topography_score': float(topography_score),
            'elevation_contribution': float(elev_score),
            'slope_contribution': float(slope_score),
            'aspect_contribution': float(aspect_score),
            'ruggedness_contribution': float(ruggedness_score),
            'terrain_metrics': metrics,
            'success': True
        }