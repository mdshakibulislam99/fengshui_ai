# Service layer for wrapping all AMap API calls and handling map data retrieval

import requests
import logging
from typing import Dict, List, Optional, Tuple
import time

from config import config

logger = logging.getLogger(__name__)


def _get_with_retry(url: str, params: Dict, timeout: int = 10) -> Optional[requests.Response]:
    def _call():
        return requests.get(url, params=params, timeout=timeout)

    response = retry_amap_call(_call)
    if response is None:
        return None

    response.raise_for_status()
    return response


def geocode_address(address: str, city: Optional[str] = None) -> Optional[Dict]:
    """
    Call AMap Geocoding API to convert address to coordinates.
    
    Args:
        address: The address to geocode
        city: Optional city name to narrow search
    
    Returns:
        Dictionary with latitude, longitude, and formatted_address
        or None if geocoding fails
    """
    try:
        params = {
            'key': config.AMAP_API_KEY,
            'address': address,
            'output': 'json'
        }
        
        if city:
            params['city'] = city
        
        logger.info(f"Geocoding address: {address}")
        
        response = _get_with_retry(config.AMAP_GEOCODE_URL, params, timeout=10)
        if response is None:
            return None
        
        data = response.json()
        
        if data.get('status') == '1' and data.get('geocodes'):
            geocode = data['geocodes'][0]
            location = geocode['location'].split(',')
            
            result = {
                'longitude': float(location[0]),
                'latitude': float(location[1]),
                'formatted_address': geocode.get('formatted_address', address)
            }
            
            logger.info(f"Geocoding successful: {result}")
            return result
        else:
            logger.warning(f"Geocoding failed: {data.get('info')}")

            # Fallback 1: place text search — most precise for POI names.
            text_result = geocode_via_place_text(address, city)
            if text_result:
                logger.info(f"Geocoding resolved via place text search: {text_result}")
                return text_result

            # Fallback 2: input tips often resolves detailed POI/area names that
            # are rejected by strict geocode parsing.
            tips_result = geocode_via_input_tips(address, city)
            if tips_result:
                logger.info(f"Geocoding resolved via input tips: {tips_result}")
                return tips_result

            return None
            
    except Exception as e:
        logger.error(f"Error calling geocoding API: {str(e)}")
        return None


def get_input_tips(keyword: str, city: str = '', limit: int = 5) -> List[Dict]:
    """Fetch search suggestions (input tips) from AMap."""
    try:
        cleaned_keyword = (keyword or '').strip()
        if not cleaned_keyword:
            return []

        limit = max(1, min(int(limit), 10))

        params = {
            'key': config.AMAP_API_KEY,
            'keywords': cleaned_keyword,
            'city': city,
            'citylimit': 'false',
            'datatype': 'all',
            'output': 'json'
        }

        response = _get_with_retry('https://restapi.amap.com/v3/assistant/inputtips', params, timeout=6)
        if response is None:
            return []

        data = response.json()
        if data.get('status') != '1':
            logger.warning(f"Input tips failed: {data.get('info')}")
            return []

        tips = data.get('tips', [])
        parsed = []

        for tip in tips:
            name = str(tip.get('name', '')).strip()
            district = str(tip.get('district', '')).strip()
            address = str(tip.get('address', '')).strip()
            location = str(tip.get('location', '')).strip()

            if not name:
                continue

            lng = None
            lat = None
            if location and ',' in location:
                parts = location.split(',')
                if len(parts) == 2:
                    try:
                        lng = float(parts[0])
                        lat = float(parts[1])
                    except (TypeError, ValueError):
                        lng = None
                        lat = None

            parsed.append({
                'name': name,
                'district': district,
                'address': address,
                'display': ' '.join([v for v in [district, address] if v]).strip(),
                'longitude': lng,
                'latitude': lat
            })

            if len(parsed) >= limit:
                break

        return parsed

    except Exception as e:
        logger.error(f"Error fetching input tips: {str(e)}")
        return []


def geocode_via_input_tips(address: str, city: Optional[str] = None) -> Optional[Dict]:
    """Fallback geocoding via AMap input tips endpoint."""
    try:
        tips = get_input_tips(address, city or '', limit=8)
        for tip in tips:
            lng = tip.get('longitude')
            lat = tip.get('latitude')
            if lng is None or lat is None:
                continue
            return {
                'longitude': float(lng),
                'latitude': float(lat),
                'formatted_address': tip.get('display') or tip.get('name') or address
            }
    except Exception as e:
        logger.warning(f"Input tips geocode fallback failed: {e}")
    return None


def geocode_via_place_text(address: str, city: Optional[str] = None) -> Optional[Dict]:
    """Fallback geocoding via AMap place text search endpoint."""
    try:
        params = {
            'key': config.AMAP_API_KEY,
            'keywords': address,
            'output': 'json',
            'offset': 1,
            'page': 1,
            'extensions': 'base',
            'citylimit': 'false'
        }
        if city:
            params['city'] = city

        response = _get_with_retry('https://restapi.amap.com/v3/place/text', params, timeout=8)
        if response is None:
            return None

        data = response.json()
        pois = data.get('pois') or []
        if data.get('status') != '1' or not pois:
            return None

        first = pois[0]
        location = str(first.get('location', '')).split(',')
        if len(location) != 2:
            return None

        return {
            'longitude': float(location[0]),
            'latitude': float(location[1]),
            'formatted_address': first.get('name') or first.get('address') or address
        }
    except Exception as e:
        logger.warning(f"Place text geocode fallback failed: {e}")
        return None


def search_nearby_pois(longitude: float, latitude: float, radius: int = 500) -> Dict[str, List[Dict]]:
    """
    Search for nearby Points of Interest (POI) around a location.
    Falls back to OpenStreetMap Overpass API if AMap hits rate limits.
    
    Args:
        longitude: Longitude of center point
        latitude: Latitude of center point
        radius: Search radius in meters
    
    Returns:
        Dictionary with categorized POI data:
        {
            'parks': [...],
            'water': [...],
            'buildings': [...],
            ...
        }
    """
    logger.info(f"Searching POIs near ({longitude}, {latitude}) with radius {radius}m")
    
    poi_results = {}
    location_str = f"{longitude},{latitude}"
    rate_limited_categories = []
    
    # Search for each POI category via AMap
    for category_name, category_code in config.POI_CATEGORIES.items():
        try:
            params = {
                'key': config.AMAP_API_KEY,
                'location': location_str,
                'radius': radius,
                'types': category_code,
                'offset': config.POI_PAGE_SIZE,
                'output': 'json',
                'extensions': 'all'
            }
            
            response = _get_with_retry(config.AMAP_POI_SEARCH_URL, params, timeout=10)
            if response is None:
                poi_results[category_name] = []
                rate_limited_categories.append(category_name)
                continue
            
            data = response.json()
            
            if data.get('status') == '1':
                pois = data.get('pois', [])
                poi_results[category_name] = parse_pois(pois)
                logger.info(f"Found {len(pois)} POIs for category: {category_name}")
                # If buildings returned 0 results, flag for Baidu fallback
                if category_name == 'buildings' and len(pois) == 0:
                    rate_limited_categories.append(category_name)
            else:
                info = data.get('info', '')
                logger.warning(f"POI search failed for {category_name}: {info}")
                poi_results[category_name] = []
                # Detect rate limit / quota exceeded
                if 'CUQPS' in info or 'EXCEEDED' in info or 'LIMIT' in info or data.get('infocode') in ('10003', '10004'):
                    rate_limited_categories.append(category_name)
            
            # Rate limiting - avoid hitting API too quickly
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error searching POIs for {category_name}: {str(e)}")
            poi_results[category_name] = []
    
    # --- Fallback chain for rate-limited categories: Baidu → OSM ---
    if rate_limited_categories:
        logger.info(f"⚠️ AMap rate-limited {len(rate_limited_categories)} categories: {rate_limited_categories}")
        
        # Fallback 1: Baidu Maps (especially good for buildings)
        if 'buildings' in rate_limited_categories:
            logger.info(f"🗺️ Trying Baidu Maps fallback for buildings...")
            try:
                from baidu_service import search_buildings_baidu
                buildings = search_buildings_baidu(longitude, latitude, radius)
                if buildings:
                    poi_results['buildings'] = buildings
                    rate_limited_categories.remove('buildings')
                    logger.info(f"✓ Baidu fallback provided {len(buildings)} buildings")
            except Exception as e:
                logger.debug(f"Baidu fallback failed: {e}")
        
        # Fallback 2: OpenStreetMap Overpass
        if rate_limited_categories:
            logger.info(f"🌍 Falling back to OpenStreetMap Overpass API...")
            try:
                from osm_fallback import search_nearby_pois_osm
                osm_data = search_nearby_pois_osm(longitude, latitude, radius, rate_limited_categories)
                for cat in rate_limited_categories:
                    if osm_data.get(cat):
                        poi_results[cat] = osm_data[cat]
                        logger.info(f"✓ OSM fallback provided {len(osm_data[cat])} POIs for {cat}")
            except Exception as e:
                logger.error(f"OSM fallback failed: {e}")
    
    return poi_results


def parse_pois(pois: List[Dict]) -> List[Dict]:
    """
    Parse POI data from AMap API response.
    
    Args:
        pois: List of POI dictionaries from API
    
    Returns:
        List of simplified POI dictionaries
    """
    parsed = []
    
    for poi in pois:
        try:
            location = poi.get('location', '').split(',')
            if len(location) == 2:
                parsed.append({
                    'name': poi.get('name', ''),
                    'type': poi.get('type', ''),
                    'longitude': float(location[0]),
                    'latitude': float(location[1]),
                    'address': poi.get('address', ''),
                    'distance': float(poi.get('distance', 0)),
                    'area': poi.get('area', ''),
                })
        except Exception as e:
            logger.warning(f"Error parsing POI: {str(e)}")
            continue
    
    return parsed


def get_road_network_data(longitude: float, latitude: float, radius: int = 500) -> Dict:
    """
    Fetch nearby road network data including road geometry and intersections.
    
    Note: AMap doesn't have a direct road network API. We approximate this
    by searching for transportation-related POIs and road features.
    
    Args:
        longitude: Longitude of center point
        latitude: Latitude of center point
        radius: Search radius in meters
    
    Returns:
        Dictionary with road network data:
        {
            'roads': [...],
            'intersections': [...],
            'road_count': int
        }
    """
    logger.info(f"Fetching road network data near ({longitude}, {latitude})")
    
    try:
        # Search for road and transportation features
        location_str = f"{longitude},{latitude}"
        
        params = {
            'key': config.AMAP_API_KEY,
            'location': location_str,
            'radius': radius,
            'types': '150700|150701|150702',  # Roads and intersections
            'offset': config.POI_PAGE_SIZE,
            'output': 'json'
        }
        
        response = _get_with_retry(config.AMAP_POI_SEARCH_URL, params, timeout=10)
        if response is None:
            return {'roads': [], 'intersections': [], 'road_count': 0}
        
        data = response.json()
        
        if data.get('status') == '1':
            pois = data.get('pois', [])
            roads = parse_road_features(pois)
            
            # Extract intersection points (simplified)
            intersections = extract_intersections(roads)
            
            road_count = len(roads)
            
            # If AMap returns too few roads (likely sparse data), try OSM fallback
            if road_count < 5:
                logger.info(f"⚠️ AMap returned only {road_count} roads (sparse), trying OSM fallback...")
                try:
                    from osm_fallback import get_road_network_data_osm
                    osm_result = get_road_network_data_osm(longitude, latitude, radius)
                    if osm_result.get('road_count', 0) >= 5:
                        logger.info(f"✅ OSM returned {osm_result['road_count']} roads, using OSM data")
                        return osm_result
                except Exception as osm_e:
                    logger.warning(f"OSM road fallback failed: {osm_e}")
                # If OSM fallback didn't help or failed, return AMap's sparse data
            
            return {
                'roads': roads,
                'intersections': intersections,
                'road_count': road_count
            }
        else:
            info = data.get('info', '')
            logger.warning(f"Road network search failed: {info}")
            # Fall back to OSM if rate limited or on error
            if 'CUQPS' in info or 'EXCEEDED' in info or 'LIMIT' in info or 'error' in info.lower():
                logger.info("🌍 Falling back to OSM for road network data...")
                try:
                    from osm_fallback import get_road_network_data_osm
                    return get_road_network_data_osm(longitude, latitude, radius)
                except Exception as osm_e:
                    logger.error(f"OSM road fallback failed: {osm_e}")
            return {'roads': [], 'intersections': [], 'road_count': 0}
            
    except Exception as e:
        logger.error(f"Error fetching road network data: {str(e)}")
        return {'roads': [], 'intersections': [], 'road_count': 0}


def parse_road_features(pois: List[Dict]) -> List[Dict]:
    """
    Parse road features from POI data.
    
    Args:
        pois: List of POI dictionaries
    
    Returns:
        List of road feature dictionaries
    """
    roads = []
    
    for poi in pois:
        try:
            location = poi.get('location', '').split(',')
            if len(location) == 2:
                roads.append({
                    'name': poi.get('name', ''),
                    'type': poi.get('type', ''),
                    'longitude': float(location[0]),
                    'latitude': float(location[1]),
                })
        except Exception as e:
            logger.warning(f"Error parsing road feature: {str(e)}")
            continue
    
    return roads


def extract_intersections(roads: List[Dict]) -> List[Dict]:
    """
    Extract intersection points from road data.
    
    Args:
        roads: List of road dictionaries
    
    Returns:
        List of intersection points
    """
    intersections = []
    
    # First try to find roads explicitly marked as intersections/junctions
    for road in roads:
        if 'intersection' in road.get('name', '').lower() or \
           'junction' in road.get('name', '').lower() or \
           'crossing' in road.get('name', '').lower():
            intersections.append({
                'longitude': road['longitude'],
                'latitude': road['latitude'],
                'name': road.get('name', '')
            })
    
    # If we found explicit intersections, return them
    if intersections:
        return intersections
    
    # Otherwise, estimate intersections from road count
    # Assumption: ~80% of roads in an area are connected at intersections
    # So for N roads, we expect roughly 0.8*N intersection points
    if roads:
        estimated_count = max(1, int(len(roads) * 0.8))
        # Use the roads with best (shortest distance) as intersection points
        sorted_roads = sorted(roads, key=lambda r: r.get('distance', float('inf')))
        for i, road in enumerate(sorted_roads[:estimated_count]):
            intersections.append({
                'longitude': road['longitude'],
                'latitude': road['latitude'],
                'name': f"Intersection{i+1}"
            })
    
    return intersections


def calculate_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    
    Args:
        lon1, lat1: First coordinate
        lon2, lat2: Second coordinate
    
    Returns:
        Distance in meters
    """
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000  # Earth radius in meters
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c

def reverse_geocode_coordinates(longitude: float, latitude: float) -> Optional[Dict]:
    """
    Call AMap Reverse Geocoding API to convert coordinates to address.
    
    Args:
        longitude: Longitude of the point
        latitude: Latitude of the point
    
    Returns:
        Dictionary with address information or None if reverse geocoding fails
    """
    try:
        params = {
            'key': config.AMAP_API_KEY,
            'location': f"{longitude},{latitude}",
            'output': 'json'
        }
        
        logger.info(f"Reverse geocoding: ({longitude}, {latitude})")
        
        response = _get_with_retry('https://restapi.amap.com/v3/geocode/regeo', params, timeout=10)
        if response is None:
            return None
        
        data = response.json()
        
        if data.get('status') == '1' and data.get('regeocode'):
            regeocode = data['regeocode']
            
            result = {
                'formatted_address': regeocode.get('formatted_address'),
                'province': regeocode.get('province'),
                'city': regeocode.get('city'),
                'district': regeocode.get('district'),
                'address_component': regeocode.get('addressComponent')
            }
            
            logger.info(f"Reverse geocoding successful: {result['formatted_address']}")
            return result
        else:
            logger.warning(f"Reverse geocoding failed: {data.get('info')}")
            return None
            
    except Exception as e:
        logger.error(f"Error in reverse geocoding: {str(e)}")
        return None


def retry_amap_call(func, max_retries=3, base_delay=0.5):
    """
    Wrapper function for retrying AMap API calls with exponential backoff.
    
    Args:
        func: Function to call
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
    
    Returns:
        Result of the function call or None on failure
    """
    for attempt in range(max_retries):
        try:
            return func()
        except (requests.Timeout, requests.ConnectionError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} retries: {str(e)}")
                return None
            
            delay = base_delay * (2 ** attempt)
            logger.warning(f"API call failed, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Non-retryable error: {str(e)}")
            return None