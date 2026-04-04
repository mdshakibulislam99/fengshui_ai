# HydroSHEDS (River Network) Configuration

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str, default: bool = True) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


class HydroSHEDSConfig:
    """Configuration for HydroSHEDS river analysis via Google Earth Engine."""

    HYDROSHEDS_ENABLE = _as_bool(os.getenv('HYDROSHEDS_ENABLE'), True)

    # Reuse DEM service account by default so setup remains simple.
    HYDROSHEDS_DIR = Path(__file__).parent
    HYDROSHEDS_GEE_SERVICE_ACCOUNT_PATH = os.getenv(
        'HYDROSHEDS_GEE_SERVICE_ACCOUNT_PATH',
        str(HYDROSHEDS_DIR.parent / 'dem' / 'service_account.json')
    )

    # HydroSHEDS flow accumulation image in Earth Engine.
    # Typical values: WWF/HydroSHEDS/15ACC (15 arc-second), WWF/HydroSHEDS/03ACC (3 arc-second)
    HYDROSHEDS_FLOW_ACC_DATASET = os.getenv('HYDROSHEDS_FLOW_ACC_DATASET', 'WWF/HydroSHEDS/15ACC')

    # Parameters for deriving river-like channels from flow accumulation.
    # Minimum flow accumulation threshold (adaptive thresholding is also used at runtime).
    HYDROSHEDS_FLOW_ACC_THRESHOLD = int(os.getenv('HYDROSHEDS_FLOW_ACC_THRESHOLD', '1'))

    # Pixel size for analysis. HydroSHEDS 15ACC is ~500m; keep tunable for stability/performance.
    HYDROSHEDS_PIXEL_SIZE_M = int(os.getenv('HYDROSHEDS_PIXEL_SIZE_M', '500'))
    HYDROSHEDS_RADIUS_M = int(os.getenv('HYDROSHEDS_RADIUS_M', '1000'))
    HYDROSHEDS_CACHE_SIZE = int(os.getenv('HYDROSHEDS_CACHE_SIZE', '128'))


hydrosheds_config = HydroSHEDSConfig()
