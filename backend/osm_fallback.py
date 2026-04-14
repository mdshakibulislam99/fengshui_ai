"""
OpenStreetMap Overpass API fallback for POI and road data.

Used when AMap API hits rate limits (CUQPS_HAS_EXCEEDED_THE_LIMIT).
Overpass API is free, no API key, no daily quota.
"""

import logging
import math
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Overpass API endpoints (multiple mirrors for reliability)
OVERPASS_ENDPOINTS = [
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
]

# Map AMap POI categories to OSM tags
# Each entry: (OSM key, OSM values list)
OSM_TAG_MAP = {
    'parks': [
        ('leisure', ['park', 'garden', 'nature_reserve']),
        ('landuse', ['recreation_ground', 'grass']),
    ],
    'water': [
        ('natural', ['water', 'wetland', 'spring']),
        ('waterway', ['river', 'stream', 'canal', 'lake', 'pond']),
    ],
    'buildings': [
        ('building', ['commercial', 'office', 'retail', 'industrial', 'public']),
    ],
    'residential': [
        ('building', ['residential', 'apartments', 'house', 'dormitory']),
        ('landuse', ['residential']),
    ],
    'hospitals': [
        ('amenity', ['hospital', 'clinic', 'doctors', 'pharmacy']),
    ],
    'schools': [
        ('amenity', ['school', 'university', 'college', 'kindergarten', 'library']),
    ],
    'temples': [
        ('amenity', ['place_of_worship']),
        ('building', ['temple', 'church', 'mosque']),
    ],
    'transportation': [
        ('highway', ['bus_stop']),
        ('railway', ['station', 'halt']),
        ('amenity', ['bus_station', 'ferry_terminal']),
        ('public_transport', ['station', 'stop_position']),
    ],
}


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two lat/lon points."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _build_overpass_query(latitude: float, longitude: float, radius: int,
                          categories: List[str]) -> str:
    """
    Build an Overpass QL query that fetches all requested categories in one request.
    """
    parts = []
    for cat in categories:
        tag_groups = OSM_TAG_MAP.get(cat, [])
        for osm_key, osm_values in tag_groups:
            for val in osm_values:
                parts.append(f'  node["{osm_key}"="{val}"](around:{radius},{latitude},{longitude});')
                parts.append(f'  way["{osm_key}"="{val}"](around:{radius},{latitude},{longitude});')

    query = f"""[out:json][timeout:15];
(
{chr(10).join(parts)}
);
out center body;"""
    return query


def _build_road_query(latitude: float, longitude: float, radius: int) -> str:
    """Build Overpass query for road network data."""
    return f"""[out:json][timeout:15];
(
  way["highway"~"^(primary|secondary|tertiary|residential|unclassified|trunk|motorway)$"](around:{radius},{latitude},{longitude});
);
out center body;"""


def _call_overpass(query: str) -> Optional[dict]:
    """Call Overpass API with fallback endpoints."""
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            resp = requests.post(
                endpoint,
                data={'data': query},
                timeout=(2, 6),
                headers={'Accept': 'application/json'}
            )
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                logger.warning(f"Overpass endpoint {endpoint} rate limited, trying next")
                continue
            else:
                logger.warning(f"Overpass {endpoint} returned {resp.status_code}")
                continue
        except (requests.Timeout, requests.ConnectionError) as e:
            logger.warning(f"Overpass {endpoint} failed: {e}")
            continue
        except Exception as e:
            logger.error(f"Overpass unexpected error: {e}")
            continue
    logger.error("All Overpass endpoints failed")
    return None


def _element_to_poi(element: dict, center_lat: float, center_lon: float) -> Optional[dict]:
    """Convert an Overpass element to our standard POI format."""
    # Get coordinates (nodes have lat/lon directly; ways have center)
    lat = element.get('lat') or (element.get('center', {}).get('lat'))
    lon = element.get('lon') or (element.get('center', {}).get('lon'))

    if lat is None or lon is None:
        return None

    tags = element.get('tags', {})
    name = tags.get('name', tags.get('name:en', tags.get('name:zh', '')))
    poi_type = tags.get('amenity') or tags.get('leisure') or tags.get('building') or tags.get('natural') or ''
    distance = _haversine_distance(center_lat, center_lon, lat, lon)

    return {
        'name': name,
        'type': poi_type,
        'longitude': lon,
        'latitude': lat,
        'address': tags.get('addr:street', ''),
        'distance': round(distance, 1),
        'area': '',
        '_source': 'osm',
    }


def _classify_element(element: dict) -> List[str]:
    """Determine which categories an OSM element belongs to."""
    tags = element.get('tags', {})
    categories = []

    for category, tag_groups in OSM_TAG_MAP.items():
        for osm_key, osm_values in tag_groups:
            tag_val = tags.get(osm_key, '')
            if tag_val in osm_values:
                categories.append(category)
                break  # one match per category is enough

    return categories


def search_nearby_pois_osm(longitude: float, latitude: float,
                           radius: int = 500,
                           categories: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
    """
    Search for nearby POIs using OpenStreetMap Overpass API.
    Drop-in replacement for amap_service.search_nearby_pois().

    Args:
        longitude: Center longitude
        latitude: Center latitude
        radius: Search radius in meters
        categories: Specific categories to fetch (default: all)

    Returns:
        Dict with same structure as AMap: {'parks': [...], 'hospitals': [...], ...}
    """
    if categories is None:
        categories = list(OSM_TAG_MAP.keys())

    logger.info(f"🌍 OSM fallback: searching POIs near ({latitude:.4f}, {longitude:.4f}), "
                f"radius={radius}m, categories={categories}")

    result = {cat: [] for cat in categories}

    query = _build_overpass_query(latitude, longitude, radius, categories)
    data = _call_overpass(query)
    if data is None:
        logger.warning("OSM fallback: Overpass query failed, returning empty")
        return result

    elements = data.get('elements', [])
    logger.info(f"🌍 OSM fallback: received {len(elements)} elements")

    for el in elements:
        poi = _element_to_poi(el, latitude, longitude)
        if poi is None:
            continue

        matched_cats = _classify_element(el)
        for cat in matched_cats:
            if cat in result:
                result[cat].append(poi)

    for cat in categories:
        logger.info(f"  OSM {cat}: {len(result[cat])} found")

    return result


def get_road_network_data_osm(longitude: float, latitude: float,
                              radius: int = 500) -> Dict:
    """
    Fetch road network data from OSM Overpass.
    Drop-in replacement for amap_service.get_road_network_data().

    Returns:
        Dict with 'roads', 'intersections', 'road_count'
    """
    logger.info(f"🌍 OSM fallback: fetching roads near ({latitude:.4f}, {longitude:.4f})")

    query = _build_road_query(latitude, longitude, radius)
    data = _call_overpass(query)

    if data is None:
        return {'roads': [], 'intersections': [], 'road_count': 0}

    elements = data.get('elements', [])
    roads = []

    for el in elements:
        if el.get('type') != 'way':
            continue
        tags = el.get('tags', {})
        center = el.get('center', {})
        lat = center.get('lat')
        lon = center.get('lon')
        if lat is None or lon is None:
            continue

        roads.append({
            'name': tags.get('name', ''),
            'type': tags.get('highway', ''),
            'longitude': lon,
            'latitude': lat,
            'distance': _haversine_distance(latitude, longitude, lat, lon),
        })

    # Estimate intersections from road count
    # Roads that share nodes are intersections; we approximate
    intersection_count = max(0, len(roads) - 1)
    intersections = [{'longitude': r['longitude'], 'latitude': r['latitude']}
                     for r in roads[:intersection_count]]

    logger.info(f"🌍 OSM fallback: {len(roads)} roads, ~{intersection_count} intersections")
    return {
        'roads': roads,
        'intersections': intersections,
        'road_count': len(roads),
    }
