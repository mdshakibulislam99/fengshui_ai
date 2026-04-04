# DEM (Digital Elevation Model) Configuration
# All DEM-related settings for OpenTopography and Google Earth Engine

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DEMConfig:
    """Configuration for DEM services (OpenTopography + Google Earth Engine)"""
    
    # OpenTopography API Configuration (Primary DEM source for China)
    OPENTOPO_API_KEY = os.getenv('OPENTOPO_API_KEY', '')
    OPENTOPO_API_URL = 'https://portal.opentopography.org/API/globaldem'
    OPENTOPO_DEM_TYPE = 'SRTMGL1'  # SRTM 30m resolution for global coverage
    
    # Google Earth Engine Configuration (Fallback source)
    DEM_DIR = Path(__file__).parent  # backend/dem/ directory
    GEE_SERVICE_ACCOUNT_PATH = str(DEM_DIR / 'service_account.json')
    GEE_ENABLE_DEM = True  # Enable DEM data for Feng Shui analysis
    
    # DEM Analysis Parameters
    DEM_RADIUS_M = 500  # Search radius for terrain analysis (meters)
    DEM_CACHE_SIZE = 128  # LRU cache size for elevation queries
    DEM_TIMEOUT = 15  # API request timeout in seconds


# Create a config instance
dem_config = DEMConfig()
