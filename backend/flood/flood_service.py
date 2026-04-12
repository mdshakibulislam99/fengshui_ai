# GEE Flood Risk Service
# Computes screening-level flood risk from surface water, terrain, and rainfall signals.

import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict

try:
    import ee
except ImportError:
    ee = None

try:
    from .config import flood_config
except ImportError:
    from config import flood_config

logger = logging.getLogger(__name__)


class GEEFloodService:
    """Flood risk screening service using Google Earth Engine datasets."""

    def __init__(self, service_account_path: str = None):
        self.service_account_path = service_account_path or flood_config.GEE_SERVICE_ACCOUNT_PATH
        self.enabled = flood_config.FLOOD_ENABLE
        self._authenticated = False

        if self.enabled:
            try:
                self._authenticate()
                logger.info("🌊 GEEFloodService initialized successfully (GEE)")
            except Exception as e:
                logger.warning(f"⚠️ GEEFloodService initialization failed: {e}")
                self.enabled = False

    def _authenticate(self):
        """Authenticate with Google Earth Engine."""
        if ee is None:
            raise RuntimeError("ee module not available")
        try:
            try:
                ee.Initialize()
                self._authenticated = True
                logger.info("✓ GEE already authenticated for flood service")
                return
            except Exception:
                pass

            import json
            with open(self.service_account_path, 'r') as f:
                credentials_data = json.load(f)
                service_account = credentials_data['client_email']

            credentials = ee.ServiceAccountCredentials(service_account, self.service_account_path)
            ee.Initialize(credentials)
            self._authenticated = True
            logger.info(f"✓ Flood service GEE authenticated with: {service_account}")

        except Exception as e:
            logger.error(f"❌ Flood service GEE authentication failed: {e}")
            raise

    @lru_cache(maxsize=256)
    def get_flood_risk_analysis(self, longitude: float, latitude: float, radius: int = None) -> Dict:
        """
        Analyze flood risk around a location.

        Returns:
            {
                'success': bool,
                'flood_scores': {
                    'flood_risk_index': float (0-100),
                    'flood_exposure_score': float (0-100),
                    'flood_level': str
                },
                'flood_metrics': {
                    'distance_to_persistent_water_m': float,
                    'surface_water_occurrence_pct': float,
                    'surface_water_seasonality_months': float,
                    'mean_slope_degrees': float,
                    'rainfall_p95_mm_day': float,
                    'heavy_rain_frequency': float
                },
                'source': str,
                'error': str (if unsuccessful)
            }
        """
        radius = int(radius or flood_config.DEFAULT_RADIUS)

        if radius <= 0:
            radius = flood_config.DEFAULT_RADIUS
        if radius > flood_config.MAX_RADIUS:
            radius = flood_config.MAX_RADIUS

        if not self.enabled:
            return {
                'success': False,
                'flood_scores': {},
                'flood_metrics': {},
                'source': 'GEE Flood',
                'error': 'Flood service is disabled'
            }

        if not self._authenticated:
            return {
                'success': False,
                'flood_scores': {},
                'flood_metrics': {},
                'source': 'GEE Flood',
                'error': 'GEE not authenticated'
            }

        try:
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(radius)

            metrics = self._fetch_flood_signals(point, region)
            scores = self._calculate_flood_scores(metrics, radius)

            logger.info(
                f"✓ Flood analysis complete: risk={scores['flood_risk_index']:.1f}/100, "
                f"level={scores['flood_level']}"
            )

            return {
                'success': True,
                'flood_scores': scores,
                'flood_metrics': metrics,
                'source': 'GEE JRC-GSW + CHIRPS + SRTM',
                'error': None
            }

        except Exception as e:
            logger.error(f"❌ Error in flood analysis: {e}")
            return {
                'success': False,
                'flood_scores': {},
                'flood_metrics': {},
                'source': 'GEE Flood',
                'error': str(e)
            }

    def _fetch_flood_signals(self, point: ee.Geometry, region: ee.Geometry) -> Dict:
        """Fetch hydrologic, terrain, and rainfall signals from GEE."""
        gsw = ee.Image(flood_config.JRC_GSW_DATASET)
        occurrence = gsw.select('occurrence')
        seasonality = gsw.select('seasonality')

        persistent_water = occurrence.gte(flood_config.PERSISTENT_WATER_OCCURRENCE_THRESHOLD)

        distance_to_water = (
            persistent_water
            .fastDistanceTransform(512, 'pixels', 'squared_euclidean')
            .sqrt()
            .multiply(flood_config.GEE_SCALE_WATER)
            .rename('water_distance')
        )

        dem = ee.Image(flood_config.DEM_DATASET).select('elevation')
        slope = ee.Terrain.slope(dem).rename('slope')

        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=365 * flood_config.RAINFALL_LOOKBACK_YEARS)

        rainfall = (
            ee.ImageCollection(flood_config.RAINFALL_DATASET)
            .filterDate(start_date.isoformat(), end_date.isoformat())
            .filterBounds(point)
            .select('precipitation')
        )

        rain_mean_img = rainfall.mean().rename('rain_mean')
        rain_p95_img = rainfall.reduce(ee.Reducer.percentile([95])).rename('rain_p95')

        heavy_rain_fraction_img = rainfall.map(
            lambda img: img.gte(flood_config.HEAVY_RAIN_THRESHOLD_MM_DAY).rename('heavy')
        ).mean().rename('heavy_rain_fraction')

        region_stats = ee.Dictionary({
            'occurrence': occurrence.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=flood_config.GEE_SCALE_WATER,
                maxPixels=flood_config.GEE_MAX_PIXELS,
                bestEffort=True
            ).get('occurrence'),
            'seasonality': seasonality.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=flood_config.GEE_SCALE_WATER,
                maxPixels=flood_config.GEE_MAX_PIXELS,
                bestEffort=True
            ).get('seasonality'),
            'water_distance': distance_to_water.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=flood_config.GEE_SCALE_WATER,
                maxPixels=flood_config.GEE_MAX_PIXELS,
                bestEffort=True
            ).get('water_distance'),
            'slope': slope.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=flood_config.GEE_SCALE_DEM,
                maxPixels=flood_config.GEE_MAX_PIXELS,
                bestEffort=True
            ).get('slope'),
            'rain_mean': rain_mean_img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=flood_config.GEE_SCALE_RAIN,
                maxPixels=flood_config.GEE_MAX_PIXELS,
                bestEffort=True
            ).get('rain_mean'),
            'rain_p95': rain_p95_img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=flood_config.GEE_SCALE_RAIN,
                maxPixels=flood_config.GEE_MAX_PIXELS,
                bestEffort=True
            ).get('rain_p95'),
            'heavy_freq': heavy_rain_fraction_img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=flood_config.GEE_SCALE_RAIN,
                maxPixels=flood_config.GEE_MAX_PIXELS,
                bestEffort=True
            ).get('heavy_rain_fraction')
        }).getInfo()

        return {
            'distance_to_persistent_water_m': float(region_stats.get('water_distance') or 2000.0),
            'surface_water_occurrence_pct': float(region_stats.get('occurrence') or 0.0),
            'surface_water_seasonality_months': float(region_stats.get('seasonality') or 0.0),
            'mean_slope_degrees': float(region_stats.get('slope') or 5.0),
            'rainfall_mean_mm_day': float(region_stats.get('rain_mean') or 0.0),
            'rainfall_p95_mm_day': float(region_stats.get('rain_p95') or 0.0),
            'heavy_rain_frequency': float(region_stats.get('heavy_freq') or 0.0),
        }

    def _calculate_flood_scores(self, metrics: Dict, radius: int) -> Dict:
        """Convert raw metrics into normalized flood-risk scores."""
        distance_m = metrics.get('distance_to_persistent_water_m', 2000.0)
        occurrence_pct = metrics.get('surface_water_occurrence_pct', 0.0)
        seasonality_months = metrics.get('surface_water_seasonality_months', 0.0)
        slope_deg = metrics.get('mean_slope_degrees', 5.0)
        rain_p95 = metrics.get('rainfall_p95_mm_day', 0.0)
        heavy_freq = metrics.get('heavy_rain_frequency', 0.0)

        if distance_m <= 100:
            water_proximity_risk = 1.0
        elif distance_m <= 500:
            water_proximity_risk = 1.0 - ((distance_m - 100) / 400.0) * 0.6
        elif distance_m <= 2000:
            water_proximity_risk = max(0.1, 0.4 - ((distance_m - 500) / 1500.0) * 0.3)
        else:
            water_proximity_risk = 0.1

        surface_water_risk = min(max(occurrence_pct / 100.0, 0.0), 1.0)

        flat_slope_threshold = max(flood_config.FLAT_SLOPE_THRESHOLD_DEG, 1.0)
        terrain_flatness_risk = max(0.0, min(1.0, (flat_slope_threshold - slope_deg) / flat_slope_threshold))

        rainfall_risk = min(1.0, max(0.0, (rain_p95 / 45.0) * 0.7 + heavy_freq * 0.3))

        weights = flood_config.FLOOD_RISK_WEIGHTS
        flood_risk_0_1 = (
            water_proximity_risk * weights['water_proximity'] +
            surface_water_risk * weights['surface_water'] +
            terrain_flatness_risk * weights['terrain_flatness'] +
            rainfall_risk * weights['rainfall_extremes']
        )

        exposure_0_1 = min(
            1.0,
            max(0.0, water_proximity_risk * 0.5 + rainfall_risk * 0.3 + (seasonality_months / 12.0) * 0.2)
        )

        flood_risk_index = round(flood_risk_0_1 * 100.0, 2)
        flood_exposure_score = round(exposure_0_1 * 100.0, 2)

        if flood_risk_index >= 75:
            flood_level = 'very_high'
        elif flood_risk_index >= 55:
            flood_level = 'high'
        elif flood_risk_index >= 35:
            flood_level = 'moderate'
        else:
            flood_level = 'low'

        return {
            'flood_risk_index': flood_risk_index,
            'flood_exposure_score': flood_exposure_score,
            'flood_level': flood_level,
            'water_proximity_risk': round(water_proximity_risk * 100.0, 2),
            'surface_water_risk': round(surface_water_risk * 100.0, 2),
            'terrain_flatness_risk': round(terrain_flatness_risk * 100.0, 2),
            'rainfall_extreme_risk': round(rainfall_risk * 100.0, 2),
        }


flood_service = GEEFloodService()
