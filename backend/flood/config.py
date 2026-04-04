# Configuration for GEE-based Flood Risk Service

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class FloodConfig:
    """Configuration for flood risk analysis using Google Earth Engine."""

    FLOOD_ENABLE = os.getenv('FLOOD_ENABLE', 'True').lower() == 'true'

    FLOOD_DIR = Path(__file__).parent

    GEE_SERVICE_ACCOUNT_PATH = os.getenv(
        'GEE_SERVICE_ACCOUNT_PATH',
        str(FLOOD_DIR.parent / 'dem' / 'service_account.json')
    )

    DEFAULT_RADIUS = 500
    MAX_RADIUS = 5000

    # Datasets
    JRC_GSW_DATASET = 'JRC/GSW1_4/GlobalSurfaceWater'
    DEM_DATASET = 'USGS/SRTMGL1_003'
    RAINFALL_DATASET = 'UCSB-CHG/CHIRPS/DAILY'

    # Thresholds and windows
    PERSISTENT_WATER_OCCURRENCE_THRESHOLD = 50  # % occurrence
    FLAT_SLOPE_THRESHOLD_DEG = 8.0
    HEAVY_RAIN_THRESHOLD_MM_DAY = 20.0
    RAINFALL_LOOKBACK_YEARS = 5

    # GEE request tuning
    GEE_SCALE_WATER = 30
    GEE_SCALE_DEM = 30
    GEE_SCALE_RAIN = 5500
    GEE_MAX_PIXELS = 1e8

    # Risk scoring weights (sum to 1.0)
    FLOOD_RISK_WEIGHTS = {
        'water_proximity': 0.30,
        'surface_water': 0.20,
        'terrain_flatness': 0.20,
        'rainfall_extremes': 0.30,
    }


flood_config = FloodConfig()
