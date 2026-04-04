# Configuration for ERA5 Wind Data Service (Google Earth Engine)

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class WindConfig:
    """Configuration for ERA5 Wind Data Service via Google Earth Engine."""
    
    # Enable/Disable wind analysis
    WIND_ENABLE = os.getenv('WIND_ENABLE', 'True').lower() == 'true'
    
    WIND_DIR = Path(__file__).parent

    # Google Earth Engine Configuration
    GEE_SERVICE_ACCOUNT_PATH = os.getenv(
        'GEE_SERVICE_ACCOUNT_PATH',
        str(WIND_DIR.parent / 'dem' / 'service_account.json')  # Reuse same GEE credentials
    )
    
    # ERA5 Dataset Configuration
    # Available ERA5 datasets on Google Earth Engine:
    # 1. ECMWF/ERA5/DAILY - Daily aggregated data (0.25° resolution ~31km)
    # 2. ECMWF/ERA5_LAND/HOURLY - Hourly land data (0.1° resolution ~11km)
    
    ERA5_DATASET = os.getenv('ERA5_DATASET', 'ECMWF/ERA5_LAND/HOURLY')
    ERA5_LAND_DATASET = os.getenv('ERA5_LAND_DATASET', 'ECMWF/ERA5_LAND/HOURLY')
    
    # Wind Analysis Parameters
    DEFAULT_RADIUS = 500  # meters (for spatial analysis)
    WIND_HEIGHT = '10m'   # Wind measurement height (10m or 100m available)
    
    # Time Range for Historical Analysis
    # ERA5 data available from 1940 to near-real-time (7 days delay)
    ANALYSIS_START_YEAR = 2020  # Start year for wind pattern analysis
    ANALYSIS_MONTHS = 12  # Number of recent months to analyze
    
    # Wind Direction Sectors (Feng Shui 8 Directions)
    WIND_DIRECTIONS = {
        'N': (337.5, 22.5),      # North
        'NE': (22.5, 67.5),      # Northeast
        'E': (67.5, 112.5),      # East
        'SE': (112.5, 157.5),    # Southeast
        'S': (157.5, 202.5),     # South
        'SW': (202.5, 247.5),    # Southwest
        'W': (247.5, 292.5),     # West
        'NW': (292.5, 337.5),    # Northwest
    }
    
    # Feng Shui Wind Direction Preferences
    # Based on traditional Feng Shui principles
    FAVORABLE_DIRECTIONS = ['S', 'SE', 'E']  # Warm, gentle winds
    NEUTRAL_DIRECTIONS = ['SW', 'NE']
    UNFAVORABLE_DIRECTIONS = ['N', 'NW', 'W']  # Cold, harsh winds
    
    # Wind Speed Categories (m/s)
    # Feng Shui prefers moderate wind flow
    WIND_SPEED_CATEGORIES = {
        'calm': (0, 1.5),           # Too stagnant
        'light': (1.5, 3.3),        # Gentle breeze (ideal)
        'moderate': (3.3, 5.5),     # Moderate breeze (good)
        'fresh': (5.5, 8.0),        # Fresh breeze (acceptable)
        'strong': (8.0, 10.8),      # Too strong
        'very_strong': (10.8, 100), # Very unfavorable
    }
    
    # Ideal wind speed range for Feng Shui (m/s)
    IDEAL_WIND_SPEED_MIN = 1.5  # Light breeze
    IDEAL_WIND_SPEED_MAX = 5.5  # Moderate breeze
    
    # Wind Exposure Scoring Weights
    WIND_SCORE_WEIGHTS = {
        'speed_optimality': 0.40,    # How close to ideal speed range
        'direction_favorability': 0.35,  # Direction alignment with Feng Shui
        'consistency': 0.25,         # Wind pattern consistency (low variance is better)
    }
    
    # Cache Configuration
    CACHE_ENABLED = True
    CACHE_EXPIRY_HOURS = 24  # Wind patterns change slowly
    
    # Logging
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # GEE Request Parameters
    GEE_SCALE = int(os.getenv('WIND_GEE_SCALE', '11000'))  # ERA5-Land ~11km
    GEE_MAX_PIXELS = 1e8
    GEE_TIMEOUT = 30000  # 30 seconds


# Create singleton instance
wind_config = WindConfig()
