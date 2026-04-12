import os
import logging
from functools import lru_cache

try:
    import ee
except ImportError:
    ee = None

from .config import HydroSHEDSConfig

logger = logging.getLogger(__name__)


class HydroSHEDSService:
    """
    Service for river analysis using HydroSHEDS datasets on Google Earth Engine.

    It derives river-channel presence using flow accumulation and computes
    proximity and density metrics for Feng Shui scoring.
    """

    def __init__(self, service_account_path: str = None):
        self.service_account_path = service_account_path or HydroSHEDSConfig.HYDROSHEDS_GEE_SERVICE_ACCOUNT_PATH
        self.flow_acc_dataset = HydroSHEDSConfig.HYDROSHEDS_FLOW_ACC_DATASET
        self.flow_acc_threshold = HydroSHEDSConfig.HYDROSHEDS_FLOW_ACC_THRESHOLD
        self.pixel_size_m = HydroSHEDSConfig.HYDROSHEDS_PIXEL_SIZE_M
        self._authenticated = False

        self._authenticate()

    def _authenticate(self):
        """Authenticate Google Earth Engine using service account credentials."""
        if ee is None:
            logger.warning("ee module not available - HydroSHEDS unavailable")
            return
        if not self.service_account_path or not os.path.exists(self.service_account_path):
            logger.warning(f"HydroSHEDS service account file not found: {self.service_account_path}")
            return

        try:
            ee.Initialize(
                ee.ServiceAccountCredentials(
                    email=None,
                    key_file=self.service_account_path
                )
            )
            self._authenticated = True
            logger.info("✓ HydroSHEDS service initialized via Google Earth Engine")
        except Exception as e:
            logger.warning(f"⚠ HydroSHEDS GEE authentication failed: {e}")

    @lru_cache(maxsize=HydroSHEDSConfig.HYDROSHEDS_CACHE_SIZE)
    def get_river_metrics(self, lon: float, lat: float, radius_m: int = None) -> dict:
        """
        Get river metrics near a location from HydroSHEDS flow accumulation.

        Returns:
            {
                'river_distance_m': float,
                'river_density': float (0-1),
                'flow_acc_value': float,
                'success': bool,
                'source': str,
                'error': str (optional)
            }
        """
        radius_m = radius_m or HydroSHEDSConfig.HYDROSHEDS_RADIUS_M

        if not self._authenticated:
            return {
                'river_distance_m': None,
                'river_density': None,
                'flow_acc_value': None,
                'success': False,
                'source': 'HydroSHEDS',
                'error': 'Google Earth Engine not authenticated'
            }

        try:
            point = ee.Geometry.Point([lon, lat])
            buffer_zone = point.buffer(radius_m)

            flow_acc = ee.Image(self.flow_acc_dataset).select(0).rename('flow_acc')

            # Build adaptive hydrologic threshold from local statistics.
            local_stats = flow_acc.reduceRegion(
                reducer=ee.Reducer.percentile([90, 95]).combine(ee.Reducer.max(), '', True),
                geometry=buffer_zone,
                scale=self.pixel_size_m,
                maxPixels=1_000_000,
                bestEffort=True
            )

            p90 = ee.Number(local_stats.get('flow_acc_p90'))
            p95 = ee.Number(local_stats.get('flow_acc_p95'))
            min_threshold = ee.Number(self.flow_acc_threshold)

            # Prefer local percentile while enforcing a configurable minimum floor.
            adaptive_threshold = p90.max(min_threshold)

            river_mask = flow_acc.gte(adaptive_threshold).rename('river_mask')

            # Distance transform from river cells (non-zero pixels in river_mask).
            distance_to_river = (
                river_mask
                .fastDistanceTransform(512, 'pixels', 'squared_euclidean')
                .sqrt()
                .multiply(self.pixel_size_m)
                .rename('river_distance')
            )

            center_flow_acc = flow_acc.sample(point, self.pixel_size_m).first().get('flow_acc')
            center_river_distance = distance_to_river.sample(point, self.pixel_size_m).first().get('river_distance')
            river_density = river_mask.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=buffer_zone,
                scale=self.pixel_size_m,
                maxPixels=1_000_000
            ).get('river_mask')

            result = ee.Dictionary({
                'flow_acc': center_flow_acc,
                'river_distance': center_river_distance,
                'river_density': river_density,
                'adaptive_threshold': adaptive_threshold,
                'flow_acc_p95': p95
            }).getInfo()

            river_distance = result.get('river_distance')
            density = result.get('river_density')
            flow_val = result.get('flow_acc')
            threshold_used = result.get('adaptive_threshold')
            p95_val = result.get('flow_acc_p95')

            success = river_distance is not None

            return {
                'river_distance_m': float(river_distance) if river_distance is not None else None,
                'river_density': float(density) if density is not None else 0.0,
                'flow_acc_value': float(flow_val) if flow_val is not None else 0.0,
                'adaptive_threshold': float(threshold_used) if threshold_used is not None else None,
                'flow_acc_p95': float(p95_val) if p95_val is not None else None,
                'success': success,
                'source': f'GEE {self.flow_acc_dataset}'
            }
        except Exception as e:
            logger.warning(f"⚠ HydroSHEDS query failed: {e}")
            return {
                'river_distance_m': None,
                'river_density': None,
                'flow_acc_value': None,
                'success': False,
                'source': 'HydroSHEDS',
                'error': str(e)
            }

    @lru_cache(maxsize=128)
    def get_river_proximity_score(self, lon: float, lat: float, radius_m: int = None) -> dict:
        """
        Convert HydroSHEDS metrics into a Feng Shui river proximity score.

        Score logic:
        - 100m-800m from river: generally optimal energetic flow
        - very close (<100m): slight penalty (flood/overpowering water qi risk)
        - far distance: gradually lower influence
        """
        radius_m = radius_m or HydroSHEDSConfig.HYDROSHEDS_RADIUS_M
        metrics = self.get_river_metrics(lon, lat, radius_m)

        if not metrics.get('success'):
            return {
                'river_proximity_score': 50.0,
                'river_density_score': 0.0,
                'combined_score': 50.0,
                'metrics': metrics,
                'success': False,
                'source': metrics.get('source', 'HydroSHEDS')
            }

        distance_m = metrics.get('river_distance_m') or (radius_m * 2)
        density = max(0.0, min(1.0, metrics.get('river_density') or 0.0))

        # Distance-based component (0-100)
        if distance_m < 100:
            distance_score = 70 + (distance_m / 100.0) * 20  # 70-90
        elif distance_m <= 800:
            deviation = abs(distance_m - 400)
            distance_score = 100 - (deviation / 400.0) * 10  # 90-100
        elif distance_m <= 2000:
            distance_score = 90 - ((distance_m - 800) / 1200.0) * 50  # 40-90
        else:
            distance_score = max(0.0, 40 - ((distance_m - 2000) / max(radius_m, 1)) * 20)

        density_score = density * 100
        combined = distance_score * 0.75 + density_score * 0.25

        return {
            'river_proximity_score': float(max(0.0, min(100.0, distance_score))),
            'river_density_score': float(max(0.0, min(100.0, density_score))),
            'combined_score': float(max(0.0, min(100.0, combined))),
            'metrics': metrics,
            'success': True,
            'source': metrics.get('source', 'HydroSHEDS')
        }
