# Configuration for Building Data Service (AMap 3D Building API)

import os
from dotenv import load_dotenv

load_dotenv()


class BuildingsConfig:
    """Configuration for AMap Building 3D Data Service."""
    
    # Enable/Disable buildings analysis
    BUILDINGS_ENABLE = os.getenv('BUILDINGS_ENABLE', 'True').lower() == 'true'
    
    # AMap API Configuration (same as main config)
    AMAP_API_KEY = os.getenv('AMAP_API_KEY', 'YOUR_AMAP_API_KEY_HERE')
    AMAP_SECURITY_KEY = os.getenv('AMAP_SECURITY_KEY', 'YOUR_AMAP_SECURITY_KEY_HERE')
    
    # AMap Building 3D API Endpoints
    # 1. Building 3D (height, polygon data)
    AMAP_BUILDING_3D_URL = 'https://restapi.amap.com/v3/place/text'  # POI search with building types
    
    # 2. Building Detail Query (for specific buildings)
    AMAP_BUILDING_DETAIL_URL = 'https://restapi.amap.com/v3/place/detail'
    
    # 3. Building Polygon Search (advanced)
    AMAP_BUILD_POLYGON_URL = 'https://restapi.amap.com/v3/place/around'
    
    # Building Analysis Parameters
    DEFAULT_RADIUS = 500  # meters
    MAX_RADIUS = 5000  # AMap limit
    
    # Building Type Categories (POI codes)
    BUILDING_TYPES = {
        'commercial': '120100',      # Office buildings, commercial buildings
        'residential': '120300',     # Residential buildings
        'government': '120200',      # Government buildings
        'industrial': '110300',      # Industrial buildings
        'cultural': '140300',        # Museums, libraries, cultural centers
        'hospitality': '120700',     # Hotels, restaurants
        'education': '141200',       # Schools, universities
        'medical': '090000',         # Hospitals, clinics
        'religious': '140800',       # Temples, churches, religious sites
        'transportation': '150700',  # Stations, parking lots
    }
    
    # Height Analysis Settings
    AVERAGE_BUILDING_HEIGHT_M = 20  # Default average height for buildings without data
    COMMERCIAL_AVG_HEIGHT_M = 25    # Commercial buildings typically taller
    RESIDENTIAL_AVG_HEIGHT_M = 15   # Residential usually shorter
    
    # Building Density Thresholds (buildings per km²)
    DENSITY_LOW = 50
    DENSITY_MEDIUM = 100
    DENSITY_HIGH = 200
    DENSITY_VERY_HIGH = 300
    
    # Height Variance Thresholds (meters)
    HEIGHT_VARIANCE_LOW = 10
    HEIGHT_VARIANCE_MEDIUM = 20
    HEIGHT_VARIANCE_HIGH = 40
    
    # Logging
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'


# Create singleton instance
buildings_config = BuildingsConfig()
