# NDVI (Vegetation) and NASA Data Configuration
# All NDVI and NASA satellite data settings

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NDVIConfig:
    """Configuration for NDVI and NASA satellite data services"""
    
    # NDVI (Normalized Difference Vegetation Index) Configuration
    NDVI_SATELLITE = 'SENTINEL2'  # Use Sentinel-2 for NDVI (higher resolution)
    NDVI_YEAR = 2024  # Year for NDVI data (uses most recent if available)
    NDVI_SEASON = 'summer'  # Season: 'spring', 'summer', 'autumn', 'winter'
    NDVI_RADIUS_M = 1000  # Search radius for vegetation analysis (meters)
    NDVI_CACHE_SIZE = 128  # LRU cache size for NDVI queries
    NDVI_TIMEOUT = 20  # API request timeout for NDVI queries (can take longer)
    
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
    
    # NASA Data API Configuration (Optional - for real-time NASA data)
    # Get your API key at: https://api.nasa.gov/
    NASA_API_KEY = os.getenv('NASA_API_KEY', 'j8IV7fGQaqoo8wGdLLqeQE7mwlak1jXbmADRZ7Ta')
    NASA_API_URL = 'https://api.nasa.gov'
    
    # NASA Data Sources
    # Landsat 8/9 (Higher resolution satellite imagery)
    # - 30m resolution, 16-day revisit cycle
    # - Available through NASA API
    LANDSAT_API_URL = 'https://api.nasa.gov'
    
    # NASA Data Caching
    NASA_DATA_CACHE_SIZE = 64  # Cache size for NASA API results
    NASA_DATA_TIMEOUT = 30  # Timeout for NASA API requests (seconds)
    
    # Data source priority: 'sentinel2', 'landsat'
    NDVI_DATA_SOURCE_PRIORITY = ['sentinel2', 'landsat']  # Try Sentinel first, then Landsat


# Create a config instance
ndvi_config = NDVIConfig()
