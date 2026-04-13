"""
Baidu Maps API Service - Fallback for buildings POI when AMap is rate-limited
Uses working query terms: 楼$教学楼$宿舍$商务楼
"""

import requests
import logging
from typing import Dict, List, Optional
import time

from config import Config

logger = logging.getLogger(__name__)


def search_buildings_baidu(
    longitude: float,
    latitude: float,
    radius: int = 500
) -> List[Dict]:
    """
    Search for buildings using Baidu Maps API.
    
    Args:
        longitude: Longitude
        latitude: Latitude
        radius: Search radius in meters (minimum search radius)
    
    Returns:
        List of building dictionaries with location data
    """
    if not Config.BAIDU_API_KEY:
        logger.warning("❌ Baidu API key not configured")
        return []
    
    try:
        # Always search in wider area - Baidu returns nearest buildings
        # even if requested radius is small
        search_radius = max(radius, 1000)
        
        params = {
            'query': '楼',  # Simple query: buildings/structures
            'location': f"{latitude},{longitude}",
            'radius': search_radius,
            'radius_limit': 'true',
            'output': 'json',
            'ak': Config.BAIDU_API_KEY,
            'page_size': 20
        }
        
        logger.info(f"🔍 Baidu buildings search: lat={latitude}, lng={longitude}, search_radius={search_radius}m")
        
        response = requests.get(
            'https://api.map.baidu.com/place/v2/search',
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 0:
            results = data.get('results', [])
            buildings = [
                {
                    'name': poi.get('name', ''),
                    'longitude': poi.get('location', {}).get('lng', 0),
                    'latitude': poi.get('location', {}).get('lat', 0),
                    'address': poi.get('address', ''),
                }
                for poi in results
            ]
            logger.info(f"✓ Baidu found {len(buildings)} buildings")
            return buildings
        else:
            status = data.get('status')
            msg = data.get('message', '')
            logger.warning(f"Baidu search failed: status={status} {msg}")
            return []
            
    except Exception as e:
        logger.error(f"Error searching Baidu buildings: {str(e)}")
        return []
