# Configuration file for storing API keys, environment variables, and application settings

import os
from dotenv import load_dotenv

load_dotenv()


def _env_float(name: str, default: float) -> float:
    """Read a float environment variable with safe fallback."""
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return float(default)

class Config:
    """Application configuration class."""
    
    # AMap API Configuration
    # Web Service key — Python backend REST calls (geocoding, POI search, etc.)
    AMAP_API_KEY = os.getenv('AMAP_API_KEY', 'YOUR_AMAP_API_KEY_HERE')
    # Web JS key + security key — browser map, tiles, panorama street view
    AMAP_WEB_JS_KEY = os.getenv('AMAP_WEB_JS_KEY', os.getenv('AMAP_API_KEY', 'YOUR_AMAP_API_KEY_HERE'))
    AMAP_SECURITY_KEY = os.getenv('AMAP_SECURITY_KEY', '')
    
    # API Endpoints
    AMAP_GEOCODE_URL = 'https://restapi.amap.com/v3/geocode/geo'
    AMAP_POI_SEARCH_URL = 'https://restapi.amap.com/v3/place/around'
    AMAP_ROAD_URL = 'https://restapi.amap.com/v3/direction/walking'  # Can be adjusted
    
    # Search Parameters
    DEFAULT_RADIUS = 500  # meters
    MAX_RADIUS = 5000
    POI_PAGE_SIZE = 50  # Maximum results per request
    
    # POI Categories for Feng Shui Analysis
    POI_CATEGORIES = {
        'parks': '110100|140700',  # Parks and green spaces
        'water': '150500|150600',  # Rivers, lakes, water bodies
        'buildings': '120000',  # Commercial buildings
        'residential': '120300',  # Residential areas
        'transportation': '150700',  # Transportation facilities
        'hospitals': '090000',  # Medical facilities
        'schools': '141200',  # Educational facilities
        'temples': '140800',  # Religious sites
    }
    
    # Feature Weights for Scoring (can be adjusted)
    FEATURE_WEIGHTS = {
        'green_area_ratio': 0.20,
        'water_proximity': 0.15,
        'building_density': 0.15,
        'road_density': 0.10,
        'orientation': 0.15,
        'environmental': 0.15,
        'spiritual': 0.10
    }
    
    # Flask Configuration
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # DeepSeek AI Chatbot Configuration
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'YOUR_DEEPSEEK_API_KEY_HERE')
    DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')  # or 'deepseek-coder' for technical analysis
    DEEPSEEK_ALIGNMENT_ENABLED = os.getenv('DEEPSEEK_ALIGNMENT_ENABLED', 'false').lower() == 'true'
    DEEPSEEK_SCORE_TIMEOUT_SEC = _env_float('DEEPSEEK_SCORE_TIMEOUT_SEC', 2.2)
    SCORING_MAX_LATENCY_SEC = _env_float('SCORING_MAX_LATENCY_SEC', 8.0)

    # Weather API Configuration
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '')
    WEATHER_API_URL = os.getenv('WEATHER_API_URL', 'https://api.weatherapi.com/v1/current.json')
    WEATHER_FORECAST_API_URL = os.getenv('WEATHER_FORECAST_API_URL', 'https://api.weatherapi.com/v1/forecast.json')
    WEATHER_ASTRONOMY_API_URL = os.getenv('WEATHER_ASTRONOMY_API_URL', 'https://api.weatherapi.com/v1/astronomy.json')


# Create a config instance
config = Config()
