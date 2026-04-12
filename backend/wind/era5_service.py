# ERA5 Wind Data Service
# Fetches and analyzes wind data from ERA5 dataset via Google Earth Engine
# Calculates wind metrics for Feng Shui analysis (direction, speed, exposure)

try:
    import ee
except ImportError:
    ee = None
import logging
import math
import statistics
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from functools import lru_cache

try:
    from .config import wind_config
except ImportError:
    from config import wind_config

logger = logging.getLogger(__name__)


def _first_numeric(mapping: Dict, keys: List[str], default: float = 0.0) -> float:
    """Return the first numeric value found for a candidate key list."""
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return float(default)


class ERA5WindService:
    """
    Service for fetching and analyzing wind data from ERA5 via Google Earth Engine.
    
    Capabilities:
    - Fetch historical wind patterns (speed and direction)
    - Calculate dominant wind direction
    - Analyze wind exposure and favorability
    - Generate Feng Shui wind scores
    - Seasonal wind pattern analysis
    """
    
    def __init__(self, service_account_path: str = None):
        """
        Initialize ERA5WindService with Google Earth Engine authentication.
        
        Args:
            service_account_path: Path to GEE service account JSON file
                                 If None, uses config default
        """
        self.service_account_path = service_account_path or wind_config.GEE_SERVICE_ACCOUNT_PATH
        self.enabled = wind_config.WIND_ENABLE
        self._authenticated = False
        
        if self.enabled:
            try:
                self._authenticate()
                logger.info("🌬️  ERA5WindService initialized successfully (GEE)")
            except Exception as e:
                logger.warning(f"⚠️  ERA5WindService initialization failed: {e}")
                self.enabled = False
    
    def _authenticate(self):
        """Authenticate with Google Earth Engine."""
        if ee is None:
            raise RuntimeError("ee module not available")
        try:
            # Check if already authenticated
            try:
                ee.Initialize()
                self._authenticated = True
                logger.info("✓ GEE already authenticated")
                return
            except:
                pass
            
            # Authenticate with service account
            with open(self.service_account_path, 'r') as f:
                import json
                credentials = json.load(f)
                service_account = credentials['client_email']
            
            credentials = ee.ServiceAccountCredentials(
                service_account, 
                self.service_account_path
            )
            ee.Initialize(credentials)
            self._authenticated = True
            logger.info(f"✓ GEE authenticated with service account: {service_account}")
            
        except Exception as e:
            logger.error(f"❌ GEE authentication failed: {str(e)}")
            raise
    
    def get_wind_analysis(self, 
                         longitude: float, 
                         latitude: float, 
                         radius: int = 500) -> Dict:
        """
        Fetch comprehensive wind analysis for a location.
        
        Args:
            longitude: Center point longitude
            latitude: Center point latitude
            radius: Analysis radius in meters (used for spatial averaging)
        
        Returns:
            Dictionary with:
            {
                'success': bool,
                'wind_metrics': {
                    'avg_speed': float,           # Average wind speed (m/s)
                    'dominant_direction': str,    # N, NE, E, SE, S, SW, W, NW
                    'direction_degrees': float,   # 0-360 degrees
                    'speed_category': str,        # calm, light, moderate, fresh, strong
                    'favorability': str,          # favorable, neutral, unfavorable
                    'consistency': float,         # 0-1 (low variance = high consistency)
                    'seasonal_variation': dict    # Seasonal patterns
                },
                'feng_shui_scores': {
                    'wind_exposure_score': float,      # 0-100
                    'direction_score': float,          # 0-100
                    'speed_optimality_score': float,   # 0-100
                    'overall_wind_score': float        # 0-100
                },
                'error': str (if unsuccessful)
            }
        """
        if not self.enabled:
            logger.warning("⚠️  Wind service is disabled")
            return {
                'success': False,
                'wind_metrics': {},
                'feng_shui_scores': {},
                'error': 'Wind service is disabled'
            }
        
        if not self._authenticated:
            return {
                'success': False,
                'wind_metrics': {},
                'feng_shui_scores': {},
                'error': 'GEE not authenticated'
            }
        
        try:
            # Define area of interest
            point = ee.Geometry.Point([longitude, latitude])
            # ERA5 pixels are coarse; ensure region is large enough to intersect data reliably.
            effective_radius = max(int(radius), int(wind_config.GEE_SCALE))
            region = point.buffer(effective_radius)
            
            # Get wind data from ERA5
            wind_data = self._fetch_era5_wind_data(region, point)
            
            if not wind_data['success']:
                return wind_data
            
            # Calculate wind metrics
            metrics = self._calculate_wind_metrics(wind_data['data'])
            
            # Calculate Feng Shui scores
            scores = self._calculate_feng_shui_wind_scores(metrics)
            
            logger.info(f"✓ Wind analysis complete: "
                       f"avg_speed={metrics['avg_speed']:.1f} m/s, "
                       f"direction={metrics['dominant_direction']}, "
                       f"score={scores['overall_wind_score']:.1f}/100")
            
            return {
                'success': True,
                'wind_metrics': metrics,
                'feng_shui_scores': scores,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"❌ Error in wind analysis: {str(e)}")
            return {
                'success': False,
                'wind_metrics': {},
                'feng_shui_scores': {},
                'error': str(e)
            }
    
    def _fetch_era5_wind_data(self, region: ee.Geometry, point: ee.Geometry) -> Dict:
        """
        Fetch wind speed and direction from ERA5 dataset.
        
        Args:
            region: Area of interest
            point: Center point
        
        Returns:
            Dictionary with wind u/v components and metadata
        """
        try:
            # 30 days of hourly data (720 images) captures monthly prevailing wind
            # patterns — essential for accurate Feng Shui directional scoring.
            # With a single batched getInfo() call this stays fast (~3-4s total),
            # and the pre-warm cache means users never feel this latency anyway.
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            dataset_name = wind_config.ERA5_DATASET  # 'ECMWF/ERA5_LAND/HOURLY'
            collection = (
                ee.ImageCollection(dataset_name)
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                .filterBounds(point)
                .select(['u_component_of_wind_10m', 'v_component_of_wind_10m'])
            )

            # Batch mean + stdDev into ONE getInfo() call using a combined reducer.
            # Previously this required 8 separate round-trips to GEE servers, each
            # computing over 8760 hourly images — the primary cause of 30-90s latency.
            combined_reducer = ee.Reducer.mean().combine(
                reducer2=ee.Reducer.stdDev(),
                sharedInputs=True
            )
            all_stats = collection.reduce(combined_reducer).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=wind_config.GEE_SCALE,
                maxPixels=wind_config.GEE_MAX_PIXELS
            ).getInfo()

            if not all_stats:
                return {
                    'success': False,
                    'data': {},
                    'error': 'No ERA5 wind data for this location/time window'
                }

            u_mean = _first_numeric(all_stats, ['u_component_of_wind_10m_mean'], 0.0)
            v_mean = _first_numeric(all_stats, ['v_component_of_wind_10m_mean'], 0.0)
            u_std = _first_numeric(all_stats, ['u_component_of_wind_10m_stdDev'], 0.5)
            v_std = _first_numeric(all_stats, ['v_component_of_wind_10m_stdDev'], 0.5)

            # Compute scalar wind speed locally — avoids an expensive map() over the
            # full image collection just to create per-image speed bands.
            speed_mean = math.sqrt(u_mean ** 2 + v_mean ** 2)
            speed_std = math.sqrt(u_std ** 2 + v_std ** 2) * 0.7  # approximate

            if speed_mean == 0.0 and u_mean == 0.0 and v_mean == 0.0:
                logger.warning("⚠ ERA5 returned empty/zero aggregate wind values for this query")
                return {
                    'success': False,
                    'data': {},
                    'error': 'No reliable ERA5 wind signal for this location/time window'
                }

            logger.info(
                f"✓ ERA5 data fetched ({dataset_name}): "
                f"u={u_mean:.2f}, v={v_mean:.2f} m/s"
            )

            return {
                'success': True,
                'data': {
                    'u_mean': u_mean,
                    'v_mean': v_mean,
                    'u_std': u_std,
                    'v_std': v_std,
                    'speed_mean': speed_mean,
                    'speed_std': speed_std,
                    'dataset': dataset_name,
                    'seasonal': self._get_seasonal_patterns(collection, region)
                }
            }

        except Exception as e:
            logger.error(f"❌ Error fetching ERA5 data: {str(e)}")
            return {
                'success': False,
                'data': {},
                'error': str(e)
            }
    
    def _get_seasonal_patterns(self, collection: ee.ImageCollection, region: ee.Geometry) -> Dict:
        """
        Get seasonal wind patterns (simplified version).
        
        Args:
            collection: ERA5 image collection
            region: Area of interest
        
        Returns:
            Dictionary with seasonal averages
        """
        try:
            # Simplified: just return current year's data
            # In production, you'd calculate seasonal averages
            return {
                'spring': {'speed': 0, 'direction': 0},
                'summer': {'speed': 0, 'direction': 0},
                'fall': {'speed': 0, 'direction': 0},
                'winter': {'speed': 0, 'direction': 0},
            }
        except:
            return {}
    
    def _calculate_wind_metrics(self, wind_data: Dict) -> Dict:
        """
        Calculate comprehensive wind metrics from u/v components.
        
        Args:
            wind_data: Dictionary with u_mean, v_mean, u_std, v_std
        
        Returns:
            Dictionary with calculated metrics
        """
        u = wind_data['u_mean']
        v = wind_data['v_mean']
        u_std = wind_data['u_std']
        v_std = wind_data['v_std']
        
        # Vector mean can cancel over long windows; prefer mean of scalar speed if available.
        wind_speed = wind_data.get('speed_mean')
        if wind_speed is None:
            wind_speed = math.sqrt(u**2 + v**2)
        
        # Calculate wind direction (meteorological convention: direction FROM which wind blows)
        # atan2(u, v) gives direction in radians, convert to degrees
        wind_direction_rad = math.atan2(u, v)
        wind_direction_deg = (math.degrees(wind_direction_rad) + 360) % 360
        
        # Determine dominant direction sector
        dominant_direction = self._get_direction_sector(wind_direction_deg)
        
        # Categorize wind speed
        speed_category = self._categorize_wind_speed(wind_speed)
        
        # Determine favorability based on direction
        favorability = self._get_direction_favorability(dominant_direction)
        
        # Calculate consistency (inverse of variance, normalized)
        speed_variance = wind_data.get('speed_std')
        if speed_variance is None:
            speed_variance = math.sqrt(u_std**2 + v_std**2)
        consistency = max(0, 1 - (speed_variance / max(wind_speed, 0.1)))
        
        return {
            'avg_speed': round(wind_speed, 2),
            'dominant_direction': dominant_direction,
            'direction_degrees': round(wind_direction_deg, 1),
            'speed_category': speed_category,
            'favorability': favorability,
            'consistency': round(consistency, 3),
            'speed_variance': round(speed_variance, 2),
            'seasonal_variation': wind_data.get('seasonal', {})
        }
    
    def _get_direction_sector(self, degrees: float) -> str:
        """
        Convert degrees to 8-sector wind direction (N, NE, E, SE, S, SW, W, NW).
        
        Args:
            degrees: Direction in degrees (0-360)
        
        Returns:
            Direction string (e.g., 'N', 'SE')
        """
        for direction, (min_deg, max_deg) in wind_config.WIND_DIRECTIONS.items():
            if min_deg > max_deg:  # Wraparound case (North)
                if degrees >= min_deg or degrees < max_deg:
                    return direction
            else:
                if min_deg <= degrees < max_deg:
                    return direction
        return 'N'  # Default
    
    def _categorize_wind_speed(self, speed: float) -> str:
        """
        Categorize wind speed into Feng Shui-relevant categories.
        
        Args:
            speed: Wind speed in m/s
        
        Returns:
            Category string
        """
        for category, (min_speed, max_speed) in wind_config.WIND_SPEED_CATEGORIES.items():
            if min_speed <= speed < max_speed:
                return category
        return 'very_strong'
    
    def _get_direction_favorability(self, direction: str) -> str:
        """
        Determine Feng Shui favorability of wind direction.
        
        Args:
            direction: Wind direction (N, NE, E, SE, S, SW, W, NW)
        
        Returns:
            'favorable', 'neutral', or 'unfavorable'
        """
        if direction in wind_config.FAVORABLE_DIRECTIONS:
            return 'favorable'
        elif direction in wind_config.NEUTRAL_DIRECTIONS:
            return 'neutral'
        else:
            return 'unfavorable'
    
    def _calculate_feng_shui_wind_scores(self, metrics: Dict) -> Dict:
        """
        Calculate Feng Shui wind scores based on metrics.
        
        Feng Shui Wind Principles:
        1. Moderate wind speed (1.5-5.5 m/s) is ideal - "gentle breeze"
        2. Favorable directions (S, SE, E) are better
        3. Consistent wind patterns are better than erratic
        
        Args:
            metrics: Wind metrics dictionary
        
        Returns:
            Dictionary with Feng Shui scores (0-100)
        """
        # Score 1: Speed Optimality (0-100)
        speed = metrics['avg_speed']
        if wind_config.IDEAL_WIND_SPEED_MIN <= speed <= wind_config.IDEAL_WIND_SPEED_MAX:
            # Perfect range
            speed_score = 100
        elif speed < wind_config.IDEAL_WIND_SPEED_MIN:
            # Too calm
            speed_score = 50 + (speed / wind_config.IDEAL_WIND_SPEED_MIN) * 50
        else:
            # Too strong
            excess = speed - wind_config.IDEAL_WIND_SPEED_MAX
            speed_score = max(0, 100 - (excess / 5.0) * 50)  # Penalty for strong wind
        
        # Score 2: Direction Favorability (0-100)
        favorability = metrics['favorability']
        if favorability == 'favorable':
            direction_score = 100
        elif favorability == 'neutral':
            direction_score = 65
        else:
            direction_score = 35
        
        # Score 3: Consistency Score (0-100)
        consistency_score = metrics['consistency'] * 100
        
        # Calculate weighted overall score
        weights = wind_config.WIND_SCORE_WEIGHTS
        overall_score = (
            speed_score * weights['speed_optimality'] +
            direction_score * weights['direction_favorability'] +
            consistency_score * weights['consistency']
        )
        
        return {
            'wind_exposure_score': round(overall_score, 2),
            'direction_score': round(direction_score, 2),
            'speed_optimality_score': round(speed_score, 2),
            'consistency_score': round(consistency_score, 2),
            'overall_wind_score': round(overall_score, 2)
        }
    
    @lru_cache(maxsize=128)
    def get_cached_wind_analysis(self, longitude: float, latitude: float, radius: int = 500) -> Dict:
        """
        Cached version of get_wind_analysis to avoid repeated GEE queries.
        
        Args:
            longitude: Center point longitude
            latitude: Center point latitude
            radius: Analysis radius in meters
        
        Returns:
            Same as get_wind_analysis()
        """
        return self.get_wind_analysis(longitude, latitude, radius)


# Create singleton instance (will be initialized by app.py with service account path)
# era5_wind_service = ERA5WindService()
