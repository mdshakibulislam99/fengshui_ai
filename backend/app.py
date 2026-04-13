# Main Flask server application - handles API routes and request/response logic

import os
import sys
import time
import json
import hashlib
import threading
import shutil
from pathlib import Path


def _maybe_reexec_supported_python() -> None:
    """Relaunch with project virtualenv Python when system Python is unsupported."""
    if sys.version_info >= (3, 10):
        return

    backend_dir = Path(__file__).resolve().parent
    project_dir = backend_dir.parent
    candidates = [
        project_dir / '.venv311' / 'bin' / 'python',
        project_dir / '.venv' / 'bin' / 'python',
    ]

    system_py311 = shutil.which('python3.11')
    if system_py311:
        candidates.append(Path(system_py311))

    for candidate in candidates:
        if candidate.exists() and os.access(candidate, os.X_OK):
            # Keep CLI args unchanged while swapping to a supported interpreter.
            try:
                os.execv(str(candidate), [str(candidate), __file__, *sys.argv[1:]])
            except OSError:
                # Skip broken launchers and keep searching for a working interpreter.
                continue


if __name__ == '__main__':
    _maybe_reexec_supported_python()

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from cachetools import TTLCache
import logging
import math
import ssl

from amap_service import (
    geocode_address,
    get_input_tips,
    search_nearby_pois,
    get_road_network_data,
    reverse_geocode_coordinates
)
from feature_extractor import extract_features
from scorer import calculate_feng_shui_score
from config import Config
from dem import DEMService
from dem.config import DEMConfig
from Hydroshed import HydroSHEDSService
from Hydroshed.config import HydroSHEDSConfig
from Hydroshed.china_river_service import ChinaRiverService
from buildings_data import BuildingsService
from buildings_data.config import BuildingsConfig
from wind import ERA5WindService
from wind.config import WindConfig
from wind.cma_wind_service import CMAWindService
from flood import GEEFloodService
from flood.config import FloodConfig
from flood.local_flood_service import LocalFloodService
from ndvi import NDVIService
from ndvi.config import NDVIConfig
from indoor_analyzer import analyze_room_design, analyze_room_photos
from personal_feng_shui import analyze_personal_feng_shui
from chatbot_service import get_chatbot
from expert_validation import (
    record_expert_assessment,
    get_expert_profile,
    get_learning_summary,
    get_significant_divergences
)

# Configure structured JSON logging
class _JsonFormatter(logging.Formatter):
    def format(self, record):
        log = {
            'ts': self.formatTime(record, '%Y-%m-%dT%H:%M:%S'),
            'level': record.levelname,
            'msg': record.getMessage(),
        }
        if record.exc_info:
            log['exc'] = self.formatException(record.exc_info)
        return json.dumps(log, ensure_ascii=False)

_handler = logging.StreamHandler()
_handler.setFormatter(_JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[_handler])
logger = logging.getLogger(__name__)


def _warn_runtime_compatibility() -> None:
    """Emit actionable warnings for unsupported Python/SSL runtimes."""
    if sys.version_info < (3, 10):
        logger.warning(
            "Python %s is no longer supported by some dependencies. "
            "Upgrade to Python 3.10+ (recommended 3.11).",
            sys.version.split()[0]
        )

    if 'LibreSSL' in ssl.OPENSSL_VERSION:
        logger.warning(
            "Detected %s. Some urllib3/HTTPS features may warn or be limited. "
            "Use a Python build linked against OpenSSL 1.1.1+.",
            ssl.OPENSSL_VERSION
        )


_warn_runtime_compatibility()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# ---- TTL response cache for expensive analyze calls ----
# key = sha256(lat+lng+radius rounded), TTL = 1 hour, max 512 entries
_analyze_cache: TTLCache = TTLCache(maxsize=512, ttl=3600)
_analyze_cache_lock = threading.Lock()

# ---- Per-request timing ----
@app.before_request
def _record_start_time():
    g.start_time = time.monotonic()

@app.after_request
def _log_request(response):
    duration_ms = round((time.monotonic() - g.start_time) * 1000)
    logger.info(json.dumps({
        'event': 'request',
        'method': request.method,
        'path': request.path,
        'status': response.status_code,
        'duration_ms': duration_ms,
        'ip': request.remote_addr,
    }))
    response.headers['X-Response-Time-Ms'] = str(duration_ms)
    
    # Prevent caching of API analysis results - ensure UI always gets fresh scores
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

# Initialize DEM Service for terrain analysis
dem_service = None
if DEMConfig.GEE_ENABLE_DEM:
    try:
        dem_service = DEMService(
            DEMConfig.GEE_SERVICE_ACCOUNT_PATH,
            opentopo_api_key=DEMConfig.OPENTOPO_API_KEY,
            opentopo_api_url=DEMConfig.OPENTOPO_API_URL
        )
        logger.info("✓ DEM service initialized successfully (OpenTopography + GEE fallback)")
    except Exception as e:
        logger.warning(f"⚠ DEM service initialization failed: {e}")
        logger.warning("  Proceeding without DEM data - topography scores unavailable")
        dem_service = None

# Initialize River Service for river flow analysis
# Using China's native river network database instead of GEE
hydrosheds_service = None
if HydroSHEDSConfig.HYDROSHEDS_ENABLE:
    try:
        hydrosheds_service = ChinaRiverService()
        logger.info("✓ River service initialized successfully (China National River Network)") 
    except Exception as e:
        logger.warning(f"⚠ River service initialization failed: {e}")
        logger.warning("  Proceeding without river data - river analysis unavailable")
        hydrosheds_service = None

# Initialize Buildings Data service for 3D building analysis
buildings_service = None
if BuildingsConfig.BUILDINGS_ENABLE:
    try:
        buildings_service = BuildingsService()
        logger.info("✓ Buildings Data service initialized successfully (AMap 3D building analysis)")
    except Exception as e:
        logger.warning(f"⚠ Buildings service initialization failed: {e}")
        logger.warning("  Proceeding without Buildings data - building harmony scores unavailable")
        buildings_service = None

# Initialize Wind service for wind pattern analysis
# Using China Meteorological Administration (CMA) data instead of GEE
wind_service = None
if WindConfig.WIND_ENABLE:
    try:
        wind_service = CMAWindService()
        logger.info("✓ Wind service initialized successfully (China Meteorological Administration)")
    except Exception as e:
        logger.warning(f"⚠ Wind service initialization failed: {e}")
        logger.warning("  Proceeding without Wind data - wind analysis unavailable")
        wind_service = None

# Initialize Flood service for flood risk analysis  
# Using local computation (DEM slope + CMA rainfall) instead of GEE
flood_service = None
if FloodConfig.FLOOD_ENABLE:
    try:
        flood_service = LocalFloodService()
        logger.info("✓ Flood service initialized successfully (Local computation - no GEE)")
    except Exception as e:
        logger.warning(f"⚠ Flood service initialization failed: {e}")
        logger.warning("  Proceeding without Flood data - flood risk analysis unavailable")
        flood_service = None

# Initialize NDVI service for satellite vegetation analysis
ndvi_service = None
if NDVIConfig.NDVI_ENABLE:
    try:
        ndvi_service = NDVIService(
            service_account_path=NDVIConfig.GEE_SERVICE_ACCOUNT_PATH,
            nasa_api_key=NDVIConfig.NASA_API_KEY
        )
        logger.info("✓ GEE authenticated for NDVI analysis")
        logger.info("✓ NDVI service initialized (Sentinel-2 + MODIS free fallback)")
    except Exception as e:
        logger.warning(f"⚠ NDVI service initialization failed: {e}")
        ndvi_service = None


# ==================== UTILITY FUNCTIONS ====================

def success_response(data, status_code=200):
    """Return standardized success response."""
    return jsonify({
        "success": True,
        "data": data,
        "error": None
    }), status_code


def error_response(message, status_code=400):
    """Return standardized error response."""
    return jsonify({
        "success": False,
        "data": None,
        "error": message
    }), status_code


def validate_coordinates(lat, lng):
    """Validate latitude and longitude."""
    try:
        lat = float(lat)
        lng = float(lng)
        if not (-90 <= lat <= 90):
            return False, "Latitude must be between -90 and 90"
        if not (-180 <= lng <= 180):
            return False, "Longitude must be between -180 and 180"
        return True, (lat, lng)
    except (ValueError, TypeError):
        return False, "Coordinates must be valid numbers"


def validate_polygon_coordinates(coords):
    """Validate polygon coordinates."""
    if not isinstance(coords, list):
        return False, "Coordinates must be a list"
    if len(coords) < 3:
        return False, "Polygon must have at least 3 points"
    
    for coord in coords:
        if not isinstance(coord, (list, tuple)) or len(coord) != 2:
            return False, "Each coordinate must be [lng, lat]"
        try:
            float(coord[0])
            float(coord[1])
        except (ValueError, TypeError):
            return False, "Coordinates must be valid numbers"
    
    return True, coords


def calculate_polygon_centroid(coords):
    """Calculate the center point of a polygon."""
    if not coords:
        return None
    
    lngs = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    
    return {
        'longitude': sum(lngs) / len(lngs),
        'latitude': sum(lats) / len(lats)
    }


def calculate_polygon_area(coords):
    """Calculate polygon area in square kilometers using Shoelace formula."""
    if len(coords) < 3:
        return 0
    
    # Convert to radians for accurate calculation
    def to_radians(degrees):
        return degrees * math.pi / 180
    
    # Simplified area calculation (assumes small polygon, no projection needed)
    area = 0
    n = len(coords)
    
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    
    area = abs(area) / 2
    
    # Approximate conversion to km² (very rough)
    # At equator: 1 degree ≈ 111 km
    area_km2 = area * (111 ** 2)
    
    return area_km2


def _safe_float(value):
    try:
        if value is None or value == '':
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _dew_point_c(temp_c, humidity):
    """Estimate dew point in Celsius from temp and relative humidity."""
    t = _safe_float(temp_c)
    h = _safe_float(humidity)
    if t is None or h is None or h <= 0:
        return None

    a = 17.27
    b = 237.7
    alpha = ((a * t) / (b + t)) + math.log(max(1e-6, h / 100.0))
    dp = (b * alpha) / (a - alpha)
    return round(dp, 1)


def _heat_index_c(temp_c, humidity):
    """Estimate heat index in Celsius using NOAA formula via Fahrenheit."""
    t = _safe_float(temp_c)
    h = _safe_float(humidity)
    if t is None or h is None:
        return None

    # Below ~27C the heat index is close to ambient temperature.
    if t < 27:
        return round(t, 1)

    tf = t * 9.0 / 5.0 + 32.0
    hi_f = (
        -42.379
        + 2.04901523 * tf
        + 10.14333127 * h
        - 0.22475541 * tf * h
        - 6.83783e-3 * tf * tf
        - 5.481717e-2 * h * h
        + 1.22874e-3 * tf * tf * h
        + 8.5282e-4 * tf * h * h
        - 1.99e-6 * tf * tf * h * h
    )

    hi_c = (hi_f - 32.0) * 5.0 / 9.0
    return round(hi_c, 1)


# ==================== API ENDPOINTS ====================

@app.route('/api/config', methods=['GET'])
def get_config():
    """Return frontend configuration including AMap Web JS API key."""
    try:
        from config import config
        return success_response({
            "amap_web_key": config.AMAP_WEB_JS_KEY,
            "amap_security_key": config.AMAP_SECURITY_KEY or "",
            "api_base_url": request.host_url.rstrip('/'),
            "map_default_center": [116.397428, 39.90923],
            "map_default_zoom": 13
        })
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return error_response("Failed to load configuration", 500)


def _cache_key(lat: float, lng: float, radius: int, location_tag: str = '') -> str:
    """Stable cache key for an analyze request (rounded to ~1 m precision)."""
    normalized_tag = str(location_tag or '').strip().lower()[:128]
    raw = f"v2:{round(lat, 5)}:{round(lng, 5)}:{radius}:{normalized_tag}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _prewarm_cache(latitude: float, longitude: float, radius: int = 500, location_tag: str = '') -> None:
    """
    Run analysis in a background daemon thread and store result in cache.
    Called after a successful geocode so the result is ready before the user
    clicks Analyze — making the analysis feel instant.
    """
    ckey = _cache_key(latitude, longitude, radius, location_tag)
    with _analyze_cache_lock:
        if ckey in _analyze_cache:
            return  # already cached, nothing to do

    def _worker():
        try:
            result = _run_analysis(latitude, longitude, radius)
            result['location'] = {
                'latitude': latitude,
                'longitude': longitude,
                'radius': radius,
                'address': location_tag or None,
            }
            result['_cached'] = False
            with _analyze_cache_lock:
                _analyze_cache[ckey] = result
            logger.info(f"Pre-warm complete: lat={latitude}, lng={longitude}")
        except Exception as exc:
            logger.warning(f"Pre-warm failed (non-critical): {exc}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def _run_analysis(latitude, longitude, radius, location_context=None):
    """Run the full analysis pipeline.

    poi_data and road_data are both pure AMap HTTP requests with no shared
    state — safe to fetch in parallel, saving ~0.5-1s per request.
    """
    from concurrent.futures import ThreadPoolExecutor
    pipeline_start = time.monotonic()
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_poi  = pool.submit(search_nearby_pois, longitude, latitude, radius)
        f_road = pool.submit(get_road_network_data, longitude, latitude, radius)
        poi_data  = f_poi.result()
        road_data = f_road.result()
    data_fetch_ms = round((time.monotonic() - pipeline_start) * 1000)

    features_start = time.monotonic()
    features = extract_features(
        poi_data,
        road_data,
        longitude,
        latitude,
        radius,
        dem_service=dem_service,
        hydrosheds_service=hydrosheds_service,
        buildings_service=buildings_service,
        wind_service=wind_service,
        flood_service=flood_service,
        ndvi_service=ndvi_service,
    )
    feature_extract_ms = round((time.monotonic() - features_start) * 1000)

    score_start = time.monotonic()
    score_result = calculate_feng_shui_score(features, location_context=location_context)
    scoring_ms = round((time.monotonic() - score_start) * 1000)

    logger.info(json.dumps({
        'event': 'analysis_timing',
        'data_fetch_ms': data_fetch_ms,
        'feature_extract_ms': feature_extract_ms,
        'scoring_ms': scoring_ms,
        'total_pipeline_ms': round((time.monotonic() - pipeline_start) * 1000),
    }))

    return score_result


@app.route('/api/analyze', methods=['POST'])
def analyze_location():
    """
    Main endpoint to analyze a location's Feng Shui score.

    Expected JSON input:
    {
        "latitude": float,
        "longitude": float,
        "radius": int (meters)
    }

    Returns JSON:
    {
        "final_score": float,
        "category_scores": dict,
        "explanations": list,
        "location": dict
    }
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("No JSON data provided", 400)

        latitude = data.get('latitude')
        longitude = data.get('longitude')
        location_label = data.get('address') or data.get('location_name') or data.get('location_label')
        if isinstance(location_label, str):
            location_label = location_label.strip()
        else:
            location_label = ''
        radius = data.get('radius', 500)
        try:
            radius = int(radius)
        except (TypeError, ValueError):
            return error_response("Radius must be a number", 400)

        valid, result_or_msg = validate_coordinates(latitude, longitude)
        if not valid:
            return error_response(result_or_msg, 400)

        latitude, longitude = result_or_msg

        if radius <= 0 or radius > 5000:
            return error_response("Radius must be between 1 and 5000 meters", 400)

        # Check if user requested fresh analysis (bypass cache)
        refresh_cache = data.get('refresh_cache', False)
        
        # --- Cache check ---
        ckey = _cache_key(latitude, longitude, radius, location_label)
        if not refresh_cache:
            with _analyze_cache_lock:
                cached = _analyze_cache.get(ckey)
            if cached is not None:
                logger.info(f"Cache hit: lat={latitude}, lng={longitude}, radius={radius}m")
                cached['_cached'] = True
                if location_label:
                    cached.setdefault('location', {})['address'] = location_label
                return success_response(cached)
        else:
            logger.info(f"Cache refresh requested: lat={latitude}, lng={longitude}, radius={radius}m")

        try:
            logger.info(f"Analyzing location: lat={latitude}, lng={longitude}, radius={radius}m")

            location_context = {
                'address': location_label,
                'latitude': latitude,
                'longitude': longitude,
                'radius': radius,
            }
            result = _run_analysis(latitude, longitude, radius, location_context=location_context)
            result['location'] = {
                'latitude': latitude,
                'longitude': longitude,
                'radius': radius,
                'address': location_label or None,
            }
            result['_cached'] = False

            # Store in cache
            with _analyze_cache_lock:
                _analyze_cache[ckey] = result

            logger.info(f"Analysis complete. Final score: {result['final_score']}")
            return success_response(result)

        except Exception as e:
            logger.error(f"Error analyzing location: {str(e)}", exc_info=True)
            return error_response("Failed to analyze location", 500)

    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}", exc_info=True)
        return error_response("Server error", 500)


@app.route('/api/reverse-geocode', methods=['POST'])
def reverse_geocode():
    """
    Reverse geocode coordinates to get address name.
    
    Expected JSON input:
    {
        "latitude": float,
        "longitude": float
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("No JSON data provided", 400)
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        # Validate input
        valid, result_or_msg = validate_coordinates(latitude, longitude)
        if not valid:
            return error_response(result_or_msg, 400)
        
        latitude, longitude = result_or_msg
        
        logger.info(f"Reverse geocoding: lat={latitude}, lng={longitude}")
        
        result = reverse_geocode_coordinates(longitude, latitude)
        
        if result:
            return success_response(result)
        else:
            return error_response("Address not found for coordinates", 404)
            
    except Exception as e:
        logger.error(f"Error in reverse geocode: {str(e)}", exc_info=True)
        return error_response("Failed to reverse geocode", 500)


@app.route('/api/nearby-pois', methods=['POST'])
def nearby_pois():
    """
    Fetch nearby POIs for a point location.

    Expected JSON input:
    {
        "latitude": float,
        "longitude": float,
        "radius": int (meters)
    }
    """
    try:
        data = request.get_json()

        if not data:
            return error_response("No JSON data provided", 400)

        latitude = data.get('latitude')
        longitude = data.get('longitude')
        radius = data.get('radius', 500)

        valid, result_or_msg = validate_coordinates(latitude, longitude)
        if not valid:
            return error_response(result_or_msg, 400)

        try:
            radius = int(radius)
        except (TypeError, ValueError):
            return error_response("Radius must be a number", 400)

        if radius <= 0 or radius > 5000:
            return error_response("Radius must be between 1 and 5000 meters", 400)

        latitude, longitude = result_or_msg

        try:
            poi_data = search_nearby_pois(longitude, latitude, radius)
            return success_response(poi_data)
        except Exception as e:
            logger.error(f"Error fetching nearby POIs: {str(e)}", exc_info=True)
            return error_response("Failed to fetch nearby POIs", 500)

    except Exception as e:
        logger.error(f"Error in nearby POIs endpoint: {str(e)}", exc_info=True)
        return error_response("Server error", 500)


@app.route('/api/polygon-analysis', methods=['POST'])
def polygon_analysis():
    """
    Analyze a polygonal area for Feng Shui.
    
    Expected JSON input:
    {
        "coordinates": [[lng,lat], [lng,lat], ...],
        "radius": int (optional, for surrounding POI search)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("No JSON data provided", 400)
        
        coords = data.get('coordinates', [])
        radius = data.get('radius', 500)
        try:
            radius = int(radius)
        except (TypeError, ValueError):
            return error_response("Radius must be a number", 400)
        
        # Validate polygon coordinates
        valid, result_or_msg = validate_polygon_coordinates(coords)
        if not valid:
            return error_response(result_or_msg, 400)
        
        if radius <= 0 or radius > 5000:
            return error_response("Radius must be between 1 and 5000 meters", 400)
        
        try:
            # Calculate polygon properties
            centroid = calculate_polygon_centroid(coords)
            area = calculate_polygon_area(coords)
            
            logger.info(f"Analyzing polygon: centroid={centroid}, area={area:.2f}km²")
            
            #  Analyze from the centroid with given radius
            poi_data = search_nearby_pois(centroid['longitude'], centroid['latitude'], radius)
            road_data = get_road_network_data(centroid['longitude'], centroid['latitude'], radius)
            
            # Extract features
            features = extract_features(
                poi_data,
                road_data,
                centroid['longitude'],
                centroid['latitude'],
                radius,
                dem_service=dem_service,
                hydrosheds_service=hydrosheds_service,
                buildings_service=buildings_service,
                wind_service=wind_service,
                flood_service=flood_service,
                ndvi_service=ndvi_service
            )
            
            # Calculate score
            result = calculate_feng_shui_score(features)

            # Add standard location info so polygon mode can reuse the same UI/model rendering
            result['location'] = {
                'latitude': centroid['latitude'],
                'longitude': centroid['longitude'],
                'radius': radius
            }
            
            # Add polygon-specific info
            result['polygon'] = {
                'centroid': centroid,
                'area_km2': area,
                'num_vertices': len(coords),
                'coordinates': coords
            }
            
            logger.info(f"Polygon analysis complete. Score: {result['final_score']}")
            
            return success_response(result)
            
        except Exception as e:
            logger.error(f"Error analyzing polygon: {str(e)}", exc_info=True)
            return error_response("Failed to analyze polygon", 500)
    
    except Exception as e:
        logger.error(f"Error in polygon analysis endpoint: {str(e)}", exc_info=True)
        return error_response("Server error", 500)


@app.route('/api/geocode', methods=['POST'])
def geocode():
    """
    Geocode an address to get latitude and longitude.
    
    Expected JSON input:
    {
        "address": string,
        "city": string (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("No JSON data provided", 400)
        
        address = data.get('address')
        city = data.get('city')
        
        if not address or not isinstance(address, str):
            return error_response("Address is required and must be a string", 400)
        
        logger.info(f"Geocoding address: {address}")
        
        result = geocode_address(address, city)

        if result:
            # Fire-and-forget: start analysis in background so cache is warm
            # by the time the user clicks Analyze (default radius 500m).
            try:
                _prewarm_cache(
                    result['latitude'],
                    result['longitude'],
                    500,
                    result.get('formatted_address', '')
                )
            except Exception:
                pass  # pre-warm is best-effort, never block geocode response
            return success_response(result)
        else:
            return error_response("Address not found", 404)
            
    except Exception as e:
        logger.error(f"Error geocoding address: {str(e)}", exc_info=True)
        return error_response("Failed to geocode address", 500)


@app.route('/api/input-tips', methods=['POST'])
def input_tips():
    """Return live search suggestions for location input."""
    try:
        data = request.get_json()
        if not data:
            return error_response("No JSON data provided", 400)

        keyword = data.get('keyword', '')
        city = data.get('city', '')
        limit = data.get('limit', 5)

        if not isinstance(keyword, str) or not keyword.strip():
            return success_response({'tips': []})

        tips = get_input_tips(keyword=keyword, city=city if isinstance(city, str) else '', limit=limit)
        return success_response({'tips': tips})

    except Exception as e:
        logger.error(f"Error in input tips endpoint: {str(e)}", exc_info=True)
        return error_response("Failed to fetch input tips", 500)


@app.route('/api/weather/current', methods=['GET'])
def weather_current():
    """Return current weather using WeatherAPI for coordinates or IP fallback."""
    try:
        import requests

        api_key = Config.WEATHER_API_KEY
        if not api_key:
            return error_response("WEATHER_API_KEY is not configured", 400)

        lat = request.args.get('lat')
        lng = request.args.get('lng')
        q = request.args.get('q', '').strip()

        query = 'auto:ip'
        query_source = 'ip'
        if lat is not None and lng is not None:
            valid, result_or_msg = validate_coordinates(lat, lng)
            if not valid:
                return error_response(result_or_msg, 400)
            lat_f, lng_f = result_or_msg
            query = f"{lat_f},{lng_f}"
            query_source = 'coordinates'
        elif q:
            query = q
            query_source = 'weather-text-search'

            # Improve text search quality by resolving place text with AMap first.
            try:
                amap_point = geocode_address(q)
                if amap_point and amap_point.get('latitude') is not None and amap_point.get('longitude') is not None:
                    query = f"{amap_point['latitude']},{amap_point['longitude']}"
                    query_source = 'amap-geocode'
            except Exception as geocode_err:
                logger.warning(f"AMap geocoding fallback used for current weather: {geocode_err}")

        response = requests.get(
            Config.WEATHER_API_URL,
            params={'key': api_key, 'q': query, 'aqi': 'yes'},
            timeout=10,
        )

        if response.status_code != 200:
            logger.error("WeatherAPI error %s: %s", response.status_code, response.text)
            return error_response(f"Weather API error: {response.status_code}", 502)

        raw = response.json()
        location = raw.get('location', {})
        current = raw.get('current', {})
        condition = current.get('condition', {})

        payload = {
            'location': {
                'name': location.get('name'),
                'region': location.get('region'),
                'country': location.get('country'),
                'localtime': location.get('localtime'),
            },
            'query_source': query_source,
            'metrics': {
                'temp_c': current.get('temp_c'),
                'temp_f': current.get('temp_f'),
                'feelslike_c': current.get('feelslike_c'),
                'humidity': current.get('humidity'),
                'wind_kph': current.get('wind_kph'),
                'wind_dir': current.get('wind_dir'),
                'pressure_mb': current.get('pressure_mb'),
                'uv': current.get('uv'),
                'aqi_us_epa': (current.get('air_quality') or {}).get('us-epa-index'),
            },
            'condition': {
                'text': condition.get('text'),
                'icon': condition.get('icon'),
            }
        }

        return success_response(payload)

    except requests.Timeout:
        return error_response("Weather API request timed out", 504)
    except Exception as e:
        logger.error(f"Error in weather endpoint: {str(e)}", exc_info=True)
        return error_response("Failed to fetch weather data", 500)


@app.route('/api/weather/forecast', methods=['GET'])
def weather_forecast():
    """Return forecast weather (current + hourly + daily) using WeatherAPI."""
    try:
        import requests

        api_key = Config.WEATHER_API_KEY
        if not api_key:
            return error_response("WEATHER_API_KEY is not configured", 400)

        days = request.args.get('days', 7)
        try:
            days = int(days)
        except (TypeError, ValueError):
            days = 7
        days = max(1, min(days, 10))

        q = request.args.get('q', '').strip()
        query = q or 'auto:ip'
        query_source = 'weather-text-search' if q else 'ip'

        lat = request.args.get('lat')
        lng = request.args.get('lng')
        if lat is not None and lng is not None:
            valid, result_or_msg = validate_coordinates(lat, lng)
            if not valid:
                return error_response(result_or_msg, 400)
            lat_f, lng_f = result_or_msg
            query = f"{lat_f},{lng_f}"
            query_source = 'coordinates'
        elif q:
            # Use AMap geocode first when available, then query WeatherAPI by coordinates.
            try:
                amap_point = geocode_address(q)
                if amap_point and amap_point.get('latitude') is not None and amap_point.get('longitude') is not None:
                    query = f"{amap_point['latitude']},{amap_point['longitude']}"
                    query_source = 'amap-geocode'
            except Exception as geocode_err:
                logger.warning(f"AMap geocoding fallback used for forecast weather: {geocode_err}")

        response = requests.get(
            Config.WEATHER_FORECAST_API_URL,
            params={
                'key': api_key,
                'q': query,
                'days': days,
                'aqi': 'yes',
                'alerts': 'yes',
            },
            timeout=12,
        )

        if response.status_code != 200:
            logger.error("WeatherAPI forecast error %s: %s", response.status_code, response.text)
            return error_response(f"Weather API error: {response.status_code}", 502)

        raw = response.json()
        location = raw.get('location', {})
        current = raw.get('current', {})
        forecast_days = (raw.get('forecast') or {}).get('forecastday', [])
        alerts = ((raw.get('alerts') or {}).get('alert') or [])

        hourly = []
        for d in forecast_days[:2]:
            for h in d.get('hour', []):
                hourly.append({
                    'time': h.get('time'),
                    'temp_c': h.get('temp_c'),
                    'temp_f': h.get('temp_f'),
                    'chance_of_rain': h.get('chance_of_rain'),
                    'chance_of_snow': h.get('chance_of_snow'),
                    'condition_text': (h.get('condition') or {}).get('text'),
                    'condition_icon': (h.get('condition') or {}).get('icon'),
                    'wind_kph': h.get('wind_kph'),
                    'wind_mph': h.get('wind_mph'),
                    'humidity': h.get('humidity'),
                })

        daily = []
        for d in forecast_days:
            day = d.get('day', {})
            astro = d.get('astro', {})
            daily_chance_of_rain = day.get('daily_chance_of_rain')
            daily_chance_of_snow = day.get('daily_chance_of_snow')
            moonrise = astro.get('moonrise') or 'No moonrise today'
            moonset = astro.get('moonset') or 'No moonset today'
            moon_phase = astro.get('moon_phase') or 'Unknown'
            moon_illumination = astro.get('moon_illumination')
            if moon_illumination in (None, ''):
                moon_illumination = 0

            daily.append({
                'date': d.get('date'),
                'max_temp_c': day.get('maxtemp_c'),
                'max_temp_f': day.get('maxtemp_f'),
                'min_temp_c': day.get('mintemp_c'),
                'min_temp_f': day.get('mintemp_f'),
                'avg_temp_c': day.get('avgtemp_c'),
                'avg_temp_f': day.get('avgtemp_f'),
                'condition_text': (day.get('condition') or {}).get('text'),
                'condition_icon': (day.get('condition') or {}).get('icon'),
                'daily_chance_of_rain': 0 if daily_chance_of_rain in (None, '') else daily_chance_of_rain,
                'daily_chance_of_snow': 0 if daily_chance_of_snow in (None, '') else daily_chance_of_snow,
                'uv': day.get('uv'),
                'sunrise': astro.get('sunrise'),
                'sunset': astro.get('sunset'),
                'moonrise': moonrise,
                'moonset': moonset,
                'moon_phase': moon_phase,
                'moon_illumination': moon_illumination,
            })

        dewpoint_c = current.get('dewpoint_c')
        if dewpoint_c in (None, ''):
            dewpoint_c = _dew_point_c(current.get('temp_c'), current.get('humidity'))

        heatindex_c = current.get('heatindex_c')
        if heatindex_c in (None, ''):
            heatindex_c = _heat_index_c(current.get('temp_c'), current.get('humidity'))

        dewpoint_f = current.get('dewpoint_f')
        if dewpoint_f in (None, '') and dewpoint_c not in (None, ''):
            dewpoint_f = round((float(dewpoint_c) * 9.0 / 5.0) + 32.0, 1)

        heatindex_f = current.get('heatindex_f')
        if heatindex_f in (None, '') and heatindex_c not in (None, ''):
            heatindex_f = round((float(heatindex_c) * 9.0 / 5.0) + 32.0, 1)

        payload = {
            'location': {
                'name': location.get('name'),
                'region': location.get('region'),
                'country': location.get('country'),
                'localtime': location.get('localtime'),
                'tz_id': location.get('tz_id'),
                'lat': location.get('lat'),
                'lon': location.get('lon'),
            },
            'query_source': query_source,
            'current': {
                'temp_c': current.get('temp_c'),
                'temp_f': current.get('temp_f'),
                'feelslike_c': current.get('feelslike_c'),
                'feelslike_f': current.get('feelslike_f'),
                'humidity': current.get('humidity'),
                'wind_kph': current.get('wind_kph'),
                'wind_mph': current.get('wind_mph'),
                'wind_dir': current.get('wind_dir'),
                'gust_kph': current.get('gust_kph'),
                'gust_mph': current.get('gust_mph'),
                'pressure_mb': current.get('pressure_mb'),
                'pressure_in': current.get('pressure_in'),
                'vis_km': current.get('vis_km'),
                'vis_miles': current.get('vis_miles'),
                'uv': current.get('uv'),
                'cloud': current.get('cloud'),
                'precip_mm': current.get('precip_mm'),
                'precip_in': current.get('precip_in'),
                'dewpoint_c': dewpoint_c,
                'dewpoint_f': dewpoint_f,
                'heatindex_c': heatindex_c,
                'heatindex_f': heatindex_f,
                'windchill_c': current.get('windchill_c'),
                'windchill_f': current.get('windchill_f'),
                'is_day': current.get('is_day'),
                'last_updated': current.get('last_updated'),
                'aqi_us_epa': (current.get('air_quality') or {}).get('us-epa-index'),
                'aqi_gb_defra': (current.get('air_quality') or {}).get('gb-defra-index'),
                'pm2_5': (current.get('air_quality') or {}).get('pm2_5'),
                'pm10': (current.get('air_quality') or {}).get('pm10'),
                'co': (current.get('air_quality') or {}).get('co'),
                'no2': (current.get('air_quality') or {}).get('no2'),
                'o3': (current.get('air_quality') or {}).get('o3'),
                'so2': (current.get('air_quality') or {}).get('so2'),
                'condition_text': (current.get('condition') or {}).get('text'),
                'condition_icon': (current.get('condition') or {}).get('icon'),
            },
            'hourly': hourly,
            'daily': daily,
            'alerts': [
                {
                    'headline': a.get('headline'),
                    'severity': a.get('severity'),
                    'event': a.get('event'),
                }
                for a in alerts
            ],
        }

        return success_response(payload)

    except requests.Timeout:
        return error_response("Weather API request timed out", 504)
    except Exception as e:
        logger.error(f"Error in weather forecast endpoint: {str(e)}", exc_info=True)
        return error_response("Failed to fetch weather forecast", 500)


@app.route('/api/weather/astronomy', methods=['GET'])
def weather_astronomy():
    """Return astronomy details (sun/moon times and phase) for a location/date."""
    try:
        import requests

        api_key = Config.WEATHER_API_KEY
        if not api_key:
            return error_response("WEATHER_API_KEY is not configured", 400)

        q = request.args.get('q', '').strip()
        query = q or 'auto:ip'
        query_source = 'weather-text-search' if q else 'ip'

        lat = request.args.get('lat')
        lng = request.args.get('lng')
        if lat is not None and lng is not None:
            valid, result_or_msg = validate_coordinates(lat, lng)
            if not valid:
                return error_response(result_or_msg, 400)
            lat_f, lng_f = result_or_msg
            query = f"{lat_f},{lng_f}"
            query_source = 'coordinates'
        elif q:
            try:
                amap_point = geocode_address(q)
                if amap_point and amap_point.get('latitude') is not None and amap_point.get('longitude') is not None:
                    query = f"{amap_point['latitude']},{amap_point['longitude']}"
                    query_source = 'amap-geocode'
            except Exception as geocode_err:
                logger.warning(f"AMap geocoding fallback used for astronomy: {geocode_err}")

        dt = request.args.get('dt', '').strip()
        params = {'key': api_key, 'q': query}
        if dt:
            params['dt'] = dt

        response = requests.get(
            Config.WEATHER_ASTRONOMY_API_URL,
            params=params,
            timeout=10,
        )

        if response.status_code != 200:
            logger.error("WeatherAPI astronomy error %s: %s", response.status_code, response.text)
            return error_response(f"Weather API error: {response.status_code}", 502)

        raw = response.json()
        location = raw.get('location', {})
        astro = ((raw.get('astronomy') or {}).get('astro') or {})

        payload = {
            'query_source': query_source,
            'location': {
                'name': location.get('name'),
                'region': location.get('region'),
                'country': location.get('country'),
                'localtime': location.get('localtime'),
                'tz_id': location.get('tz_id'),
                'lat': location.get('lat'),
                'lon': location.get('lon'),
            },
            'astronomy': {
                'sunrise': astro.get('sunrise'),
                'sunset': astro.get('sunset'),
                'moonrise': astro.get('moonrise'),
                'moonset': astro.get('moonset'),
                'moon_phase': astro.get('moon_phase'),
                'moon_illumination': astro.get('moon_illumination'),
            }
        }

        return success_response(payload)

    except requests.Timeout:
        return error_response("Weather API request timed out", 504)
    except Exception as e:
        logger.error(f"Error in weather astronomy endpoint: {str(e)}", exc_info=True)
        return error_response("Failed to fetch astronomy data", 500)


@app.route('/api/indoor-analyze', methods=['POST'])
def analyze_indoor_room():
    """
    Analyze indoor room design using AI feng shui analysis.
    
    Expected JSON input:
    {
        "roomType": string (bedroom, living, office, etc.),
        "elements": list of {type, position, fengShui}
    }
    
    Returns JSON with scores, factors, and recommendations.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("No JSON data provided", 400)
        
        room_type = data.get('roomType', 'bedroom')
        elements = data.get('elements', [])
        
        if not elements:
            return error_response("No elements provided for analysis", 400)
        
        logger.info(f"Analyzing indoor room: type={room_type}, elements={len(elements)}")
        
        # Call the AI backend analysis
        result = analyze_room_design(elements, room_type)
        
        # Transform to match frontend expected format
        response_data = {
            'scores': {
                'overall': result['overall_score'],
                'ai_indoor': int(result.get('ai_score') or result['overall_score']),
                'element_balance': result['element_balance'],
                'energy_balance': result['energy_score'],
                'space_flow': result['spacial_score'],
                'functional_layout': result['functional_score'],
                'wood': int((result['element_counts']['wood'] / max(1, len(elements))) * 100),
                'fire': int((result['element_counts']['fire'] / max(1, len(elements))) * 100),
                'earth': int((result['element_counts']['earth'] / max(1, len(elements))) * 100),
                'metal': int((result['element_counts']['metal'] / max(1, len(elements))) * 100),
                'water': int((result['element_counts']['water'] / max(1, len(elements))) * 100)
            },
            'fiveElements': {
                'wood': int((result['element_counts']['wood'] / max(1, len(elements))) * 100),
                'fire': int((result['element_counts']['fire'] / max(1, len(elements))) * 100),
                'earth': int((result['element_counts']['earth'] / max(1, len(elements))) * 100),
                'metal': int((result['element_counts']['metal'] / max(1, len(elements))) * 100),
                'water': int((result['element_counts']['water'] / max(1, len(elements))) * 100)
            },
            'factors': [
                {
                    'title': 'Element Balance',
                    'score': result['element_balance'],
                    'confidence': 'High',
                    'dataSources': ['Five Elements Theory', 'Room Design Analysis'],
                    'mainIssue': 'Balance of wood, fire, earth, metal, and water elements in the space.',
                    'current': ['Elements are distributed across the room'],
                    'improve': result['recommendations'][:2] if len(result['recommendations']) > 2 else result['recommendations']
                },
                {
                    'title': 'Energy Flow (Yin-Yang)',
                    'score': result['energy_score'],
                    'confidence': 'High',
                    'dataSources': ['Yin-Yang Theory', 'Energy Balance'],
                    'mainIssue': f"Current balance: {result['energy_balance']['yin']} Yin, {result['energy_balance']['yang']} Yang elements.",
                    'current': ['Energy flow is present'],
                    'improve': [rec for rec in result['recommendations'] if 'energy' in rec.lower() or 'yang' in rec.lower() or 'yin' in rec.lower()]
                },
                {
                    'title': 'Space Flow & Layout',
                    'score': result['spacial_score'],
                    'confidence': 'Medium',
                    'dataSources': ['Space Planning', 'Feng Shui Principles'],
                    'mainIssue': f"Room has {len(elements)} elements - evaluating density and flow.",
                    'current': ['Elements are placed in the room'],
                    'improve': [rec for rec in result['recommendations'] if 'clutter' in rec.lower() or 'flow' in rec.lower()]
                },
                {
                    'title': 'Functional Design',
                    'score': result['functional_score'],
                    'confidence': 'High',
                    'dataSources': ['Room Type Analysis', room_type.title() + ' Best Practices'],
                    'mainIssue': f"Layout suitability for {room_type} functionality.",
                    'current': ['Essential elements are present'],
                    'improve': [rec for rec in result['recommendations'] if room_type in rec.lower()]
                }
            ]
        }
        
        logger.info(f"Indoor analysis complete. Overall score: {result['overall_score']}")
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"Error in indoor analyze endpoint: {str(e)}", exc_info=True)
        return error_response("Failed to analyze indoor room", 500)


@app.route('/api/indoor-photo-analyze', methods=['POST'])
def analyze_indoor_photos():
    """
    Analyze uploaded indoor room photos from multiple directions.

    Expected JSON input:
    {
        "roomType": string (optional),
        "photos": {
            "north": dataUrl|null,
            "south": dataUrl|null,
            "east": dataUrl|null,
            "west": dataUrl|null,
            "floor": dataUrl|null
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("No JSON data provided", 400)

        room_type = data.get('roomType', 'general')
        photos = data.get('photos', {})
        if not isinstance(photos, dict):
            return error_response("Invalid photos payload", 400)

        uploaded_count = sum(1 for value in photos.values() if value)
        if uploaded_count < 3:
            return error_response("At least 3 photos are required for analysis", 400)

        logger.info(
            f"Analyzing indoor photos: room_type={room_type}, uploaded={uploaded_count}"
        )

        result = analyze_room_photos(photos)
        categories = result.get('categories', {})

        response_data = {
            'overallScore': int(result.get('overall_score', 0)),
            'aiIndoorScore': int(result.get('ai_score') or result.get('overall_score', 0)),
            'categories': {
                'lighting': int(categories.get('lighting', 0)),
                'spaceFlow': int(categories.get('space_flow', 0)),
                'colorHarmony': int(categories.get('color_harmony', 0)),
                'furniture': int(categories.get('furniture_placement', 0)),
                'declutter': int(categories.get('declutter', 0)),
            },
            'recommendations': result.get('recommendations', []),
            'meta': {
                'roomType': room_type,
                'photosAnalyzed': uploaded_count,
            },
        }

        logger.info(
            f"Indoor photo analysis complete. Overall score: {response_data['overallScore']}"
        )
        return success_response(response_data)

    except Exception as e:
        logger.error(f"Error in indoor photo analyze endpoint: {str(e)}", exc_info=True)
        return error_response("Failed to analyze indoor photos", 500)


@app.route('/api/personal-feng-shui/analyze', methods=['POST'])
def analyze_personal_profile():
    """Analyze personal Feng Shui profile for an individual user."""
    try:
        data = request.get_json()
        if not data:
            return error_response("No JSON data provided", 400)

        profile = data.get('profile', data)
        if not isinstance(profile, dict):
            return error_response("Profile must be a JSON object", 400)

        result = analyze_personal_feng_shui(profile)
        logger.info(
            "Personal Feng Shui analysis complete. score=%s kua=%s",
            result.get('overall_score'),
            (result.get('personal_profile') or {}).get('kua_number')
        )
        return success_response(result)

    except ValueError as e:
        logger.error(f"Validation error in personal feng shui endpoint: {str(e)}")
        return error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Error in personal feng shui endpoint: {str(e)}", exc_info=True)
        return error_response("Failed to analyze personal feng shui profile", 500)


# ==================== AI CHATBOT ENDPOINTS ====================

@app.route('/api/chat/improve', methods=['POST'])
def chat_improve():
    """
    Get AI-powered improvement suggestions based on analysis results.
    Expects analysis data in the request body.
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("No data provided", 400)
        
        analysis_data = data.get('analysis_data')
        user_query = data.get('query', None)
        
        if not analysis_data:
            return error_response("Analysis data is required", 400)
        
        # Get chatbot instance and generate suggestions
        chatbot = get_chatbot()
        result = chatbot.get_improvement_suggestions(analysis_data, user_query)
        
        return success_response(result)
    
    except Exception as e:
        logger.error(f"Error in chat improve endpoint: {str(e)}", exc_info=True)
        return error_response("Failed to generate improvement suggestions", 500)


@app.route('/api/chat/message', methods=['POST'])
def chat_message():
    """
    General chat endpoint for conversational AI interaction.
    Supports conversation history and context.
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("No data provided", 400)
        
        message = data.get('message')
        if not message:
            return error_response("Message is required", 400)
        
        conversation_history = data.get('history', [])
        analysis_context = data.get('context', None)
        
        # Get chatbot instance and process message
        chatbot = get_chatbot()
        result = chatbot.chat(message, conversation_history, analysis_context)
        
        return success_response(result)
    
    except Exception as e:
        logger.error(f"Error in chat message endpoint: {str(e)}", exc_info=True)
        return error_response("Failed to process chat message", 500)


@app.route('/api/config/deepseek-status', methods=['GET'])
def check_deepseek_status():
    """
    Check if DeepSeek API key is configured.
    """
    try:
        chatbot = get_chatbot()
        api_key = chatbot.api_key
        
        is_configured = (
            api_key and 
            api_key != 'YOUR_DEEPSEEK_API_KEY_HERE' and
            len(api_key) > 10
        )
        
        return success_response({
            'configured': is_configured,
            'message': 'DeepSeek API is configured' if is_configured else 'DeepSeek API key not configured. Please set it up.',
            'api_url': chatbot.api_url,
            'model': chatbot.model,
            'key_preview': f"{api_key[:8]}...{api_key[-4:]}" if is_configured else None
        })
    
    except Exception as e:
        logger.error(f"Error checking DeepSeek status: {str(e)}", exc_info=True)
        return error_response("Failed to check DeepSeek status", 500)


@app.route('/api/config/test-deepseek', methods=['POST'])
def test_deepseek_api():
    """
    Test the DeepSeek API connection.
    """
    try:
        import requests
        
        chatbot = get_chatbot()
        api_key = chatbot.api_key
        
        # Check if key is configured
        if not api_key or api_key == 'YOUR_DEEPSEEK_API_KEY_HERE':
            return error_response("DeepSeek API key not configured", 400)
        
        # Send a test request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": chatbot.model,
            "messages": [
                {"role": "user", "content": "Say 'Hello, Feng Shui!' in exactly one word."}
            ],
            "max_tokens": 10,
            "temperature": 0.1
        }
        
        logger.info("Testing DeepSeek API connection...")
        
        response = requests.post(
            chatbot.api_url,
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            message_content = result['choices'][0]['message']['content']
            
            logger.info(f"DeepSeek API test successful: {message_content}")
            
            return success_response({
                'success': True,
                'message': 'DeepSeek API is working correctly!',
                'test_response': message_content,
                'usage': result.get('usage', {})
            })
        
        elif response.status_code == 401:
            logger.error("DeepSeek API test failed: Invalid API key (401)")
            return error_response("Invalid API key. Please check your DeepSeek API key.", 401)
        
        elif response.status_code == 429:
            logger.error("DeepSeek API test failed: Rate limited (429)")
            return error_response("Rate limited by DeepSeek API. Please try again later.", 429)
        
        else:
            error_msg = f"DeepSeek API error: {response.status_code}"
            logger.error(error_msg)
            return error_response(error_msg, response.status_code)
    
    except requests.Timeout:
        logger.error("DeepSeek API test failed: Request timeout")
        return error_response("DeepSeek API request timed out. Check your connection.", 500)
    
    except requests.ConnectionError:
        logger.error("DeepSeek API test failed: Connection error")
        return error_response("Cannot connect to DeepSeek API. Check your internet connection.", 500)
    
    except Exception as e:
        logger.error(f"Error testing DeepSeek API: {str(e)}", exc_info=True)
        return error_response(f"Failed to test DeepSeek API: {str(e)}", 500)


# ============================================================================
# EXPERT VALIDATION ENDPOINTS (TIER 3: Learning from Expert Feedback)
# ============================================================================

@app.route('/api/expert/submit-assessment', methods=['POST'])
def submit_expert_assessment():
    """
    Submit a Feng Shui expert assessment for model validation and learning.
    
    Request body:
    {
        "expert_id": "expert_123",
        "expert_name": "Zhang Wei",
        "location_lat": 39.9042,
        "location_lng": 116.4074,
        "location_address": "Beijing, China",
        "expert_score": 85,
        "ai_score": 78,
        "category_assessments": {
            "green_space": 85,
            "water_element": 75,
            ...
        },
        "feedback": "Good orientation but missing water element to the south",
        "confidence_level": "high"
    }
    """
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        required_fields = ['expert_id', 'expert_name', 'location_lat', 'location_lng', 
                          'location_address', 'expert_score', 'ai_score']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)
        
        # Record the assessment
        assessment = record_expert_assessment(
            expert_id=str(data['expert_id']),
            expert_name=str(data['expert_name']),
            location_lat=float(data['location_lat']),
            location_lng=float(data['location_lng']),
            location_address=str(data['location_address']),
            expert_score=float(data['expert_score']),
            ai_score=float(data['ai_score']),
            category_assessments=data.get('category_assessments', {}),
            feedback=str(data.get('feedback', '')),
            confidence_level=str(data.get('confidence_level', 'moderate'))
        )
        
        logger.info(
            f"Expert assessment recorded: {data['expert_name']} "
            f"divergence={assessment['scores']['divergence']:.1f}"
        )
        
        return success_response({
            'message': 'Expert assessment recorded successfully',
            'assessment': assessment,
            'divergence': assessment['scores']['divergence'],
            'is_significant': assessment['scores']['is_significant_divergence']
        })
    
    except ValueError as e:
        return error_response(f"Invalid numeric value: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error submitting expert assessment: {str(e)}", exc_info=True)
        return error_response(f"Failed to submit assessment: {str(e)}", 500)


@app.route('/api/expert/profile/<expert_id>', methods=['GET'])
def get_expert_profile_endpoint(expert_id):
    """
    Get an expert's profile and assessment history.
    """
    try:
        profile = get_expert_profile(expert_id)
        
        if not profile:
            return error_response(f"Expert {expert_id} not found", 404)
        
        return success_response({
            'expert_id': expert_id,
            'profile': profile['profile'],
            'assessment_count': profile['assessment_count'],
            'recent_assessments': profile['assessments']
        })
    
    except Exception as e:
        logger.error(f"Error fetching expert profile: {str(e)}", exc_info=True)
        return error_response(f"Failed to fetch expert profile: {str(e)}", 500)


@app.route('/api/expert/learning-summary', methods=['GET'])
def get_learning_summary_endpoint():
    """
    Get overall learning summary from expert validations.
    Useful for model performance metrics and improvement tracking.
    """
    try:
        summary = get_learning_summary()
        
        return success_response({
            'learning_summary': summary,
            'timestamp': datetime.datetime.now().isoformat(),
            'recommendation': summary.pop('recommendation', '')
        })
    
    except Exception as e:
        logger.error(f"Error fetching learning summary: {str(e)}", exc_info=True)
        return error_response(f"Failed to fetch learning summary: {str(e)}", 500)


@app.route('/api/expert/divergences', methods=['GET'])
def get_divergences_endpoint():
    """
    Get significant divergence cases between AI and expert assessments.
    These are high-priority areas for model improvement.
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        divergences = get_significant_divergences(limit=limit)
        
        return success_response({
            'significant_divergences': divergences,
            'count': len(divergences),
            'interpretation': 'These cases show where the AI model diverges significantly from expert assessment (>15 points difference)'
        })
    
    except Exception as e:
        logger.error(f"Error fetching divergences: {str(e)}", exc_info=True)
        return error_response(f"Failed to fetch divergences: {str(e)}", 500)


# Add datetime import safely
import datetime



@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return success_response({"status": "healthy"})


# ==================== ERROR HANDLERS ====================

@app.errorhandler(400)
def bad_request(error):
    logger.warning(f"Bad request: {str(error)}")
    return error_response("Bad request", 400)


@app.errorhandler(404)
def not_found(error):
    logger.warning(f"Not found: {str(error)}")
    return error_response("Endpoint not found", 404)


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return error_response("Internal server error", 500)


# ==================== APP STARTUP ====================


if __name__ == '__main__':
    logger.info("Starting Feng Shui Analysis API Server...")
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
