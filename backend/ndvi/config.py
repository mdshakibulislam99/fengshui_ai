# NDVI (Vegetation) Configuration - MODIS Only
# Uses free, China-accessible MODIS satellite data (no GEE or NASA API required)

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NDVIConfig:
    """Configuration for NDVI satellite data services (MODIS only - no GEE/NASA)"""

    # Set to False to disable satellite vegetation scoring (NDVI) entirely.
    NDVI_ENABLE = os.getenv('NDVI_ENABLE', 'true').lower() != 'false'

    # MODIS ORNL Configuration (Primary - Free, China-accessible)
    # No GEE or NASA API authentication required
    MODIS_ORNL_API_URL = 'https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset'
    MODIS_PRODUCT = 'MOD13Q1'  # MOD13Q1: 16-day composite, 250m resolution
    
    # NDVI (Normalized Difference Vegetation Index) Configuration
    NDVI_SATELLITE = 'MODIS'  # Use MODIS for NDVI (free, fast, China-friendly)
    NDVI_YEAR = 2024  # Year for NDVI data (uses most recent if available)
    NDVI_SEASON = 'summer'  # Season: 'spring', 'summer', 'autumn', 'winter'
    NDVI_RADIUS_M = 1000  # Search radius for vegetation analysis (meters)
    NDVI_CACHE_SIZE = 128  # LRU cache size for NDVI queries
    NDVI_TIMEOUT = 5  # Fast timeout OK for MODIS (~1-2s typical)
    
    # NDVI Score Thresholds for Feng Shui Analysis
    # NDVI ranges from -1 to 1, typically:
    # < 0: Water/non-vegetation
    # 0-0.2: Sparse vegetation/barren
    # 0.2-0.4: Moderate vegetation
    # 0.4-0.6: Good vegetation
    # > 0.6: Dense vegetation (very healthy)
    NDVI_THRESHOLDS = {
        'water': -1.0,          # Water bodies
        'bare': 0.2,            # Bare ground
        'sparse': 0.4,          # Sparse vegetation
        'moderate': 0.6,        # Moderate vegetation
        'dense': 1.0            # Dense/healthy vegetation
    }


# Create a config instance
ndvi_config = NDVIConfig()
