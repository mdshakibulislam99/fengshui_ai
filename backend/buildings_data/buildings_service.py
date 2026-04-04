# Building Data Service
# Fetches and analyzes building 3D data (heights, polygons) from AMap API
# Calculates building metrics for Feng Shui analysis (harmony, density, skyline)

import requests
import logging
import math
import statistics
from typing import Dict, List, Optional, Tuple

try:
    from .config import buildings_config
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from buildings_data.config import buildings_config

logger = logging.getLogger(__name__)


class BuildingsService:
    """
    Service for fetching and analyzing building data from AMap API.
    
    Capabilities:
    - Fetch 3D building data (heights, footprints)
    - Calculate building metrics (density, average height, variance)
    - Analyze skyline and height distribution
    - Grade building harmony for Feng Shui
    """
    
    def __init__(self):
        """Initialize BuildingsService with AMap API credentials."""
        self.api_key = buildings_config.AMAP_API_KEY
        self.security_key = buildings_config.AMAP_SECURITY_KEY
        self.enabled = buildings_config.BUILDINGS_ENABLE
        logger.info(f"🏢 BuildingsService initialized (enabled={self.enabled})")
    
    def get_building_data(self, 
                         longitude: float, 
                         latitude: float, 
                         radius: int = 500,
                         building_types: Optional[List[str]] = None) -> Dict:
        """
        Fetch building data around a location.
        
        Args:
            longitude: Center point longitude
            latitude: Center point latitude
            radius: Analysis radius in meters
            building_types: List of building type codes to search (e.g., ['120100', '120300'])
                          If None, searches all building types
        
        Returns:
            Dictionary with:
            {
                'success': bool,
                'buildings': [
                    {
                        'name': str,
                        'type': str,
                        'distance': float (meters),
                        'height': float (meters, estimated if not available),
                        'latitude': float,
                        'longitude': float,
                        'address': str,
                        'phone': str (optional)
                    }
                ],
                'metrics': {
                    'total_buildings': int,
                    'avg_height': float,
                    'max_height': float,
                    'min_height': float,
                    'height_variance': float,
                    'height_stddev': float,
                    'building_density': float (per km²),
                    'dominant_height_category': str
                },
                'error': str (if unsuccessful)
            }
        """
        if not self.enabled:
            logger.warning("⚠️  Buildings service is disabled")
            return {
                'success': False,
                'buildings': [],
                'metrics': {},
                'error': 'Buildings service is disabled'
            }
        
        try:
            # If no specific types provided, search all building categories.
            # Use a single combined query to avoid AMap QPS spikes from many back-to-back requests.
            if building_types is None:
                building_types = list(buildings_config.BUILDING_TYPES.values())

            combined_types = '|'.join([code for code in building_types if code])
            buildings = self._search_buildings_by_type(
                longitude,
                latitude,
                radius,
                combined_types
            )
            
            # Remove duplicates (same building might appear in multiple searches)
            buildings = self._deduplicate_buildings(buildings)
            
            # Calculate metrics
            metrics = self._calculate_building_metrics(buildings, radius)
            
            logger.info(f"✓ Retrieved {len(buildings)} buildings in {radius}m radius")
            logger.info(f"  Metrics: avg_height={metrics['avg_height']:.1f}m, "
                       f"density={metrics['building_density']:.1f} bldgs/km², "
                       f"variance={metrics['height_variance']:.1f}m")
            
            return {
                'success': True,
                'buildings': buildings,
                'metrics': metrics,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"❌ Error fetching building data: {str(e)}")
            return {
                'success': False,
                'buildings': [],
                'metrics': {},
                'error': str(e)
            }
    
    def _search_buildings_by_type(self, 
                                  longitude: float, 
                                  latitude: float, 
                                  radius: int,
                                  building_type: str) -> List[Dict]:
        """
        Search for buildings of a specific type using AMap POI API.
        
        Args:
            longitude: Center longitude
            latitude: Center latitude
            radius: Search radius in meters
            building_type: POI type code
        
        Returns:
            List of building dictionaries with location and estimated height
        """
        try:
            params = {
                'key': self.api_key,
                'location': f'{longitude},{latitude}',
                'types': building_type,
                'radius': min(radius, 3000),  # AMap max radius
                'page': 1,
                'pagesize': 50,  # Max results per page
                'output': 'json'
            }
            
            response = requests.get(
                buildings_config.AMAP_BUILD_POLYGON_URL,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != '1':
                logger.warning(f"⚠️  AMap building search failed: {data.get('info')}")
                return []
            
            buildings = []
            pois = data.get('pois', [])
            
            for poi in pois:
                # Calculate distance from center
                distance = self._calculate_distance(
                    longitude, latitude,
                    float(poi['location'].split(',')[0]),
                    float(poi['location'].split(',')[1])
                )
                
                # Skip if outside radius
                if distance > radius:
                    continue
                
                # Estimate building height based on type
                height = self._estimate_building_height(poi.get('type'), poi.get('name'))
                
                building = {
                    'name': poi.get('name', 'Unknown'),
                    'type': self._get_building_type_name(poi.get('type')),
                    'poi_type': poi.get('type'),
                    'distance': distance,
                    'height': height,
                    'latitude': float(poi['location'].split(',')[1]),
                    'longitude': float(poi['location'].split(',')[0]),
                    'address': poi.get('address', ''),
                    'phone': poi.get('tel', ''),
                    'area': self._estimate_building_area(poi.get('type'))
                }
                
                buildings.append(building)
            
            return buildings
            
        except Exception as e:
            logger.warning(f"⚠️  Error searching buildings type {building_type}: {str(e)}")
            return []
    
    def _deduplicate_buildings(self, buildings: List[Dict]) -> List[Dict]:
        """
        Remove duplicate buildings (same location, similar names).
        
        Args:
            buildings: List of building dictionaries
        
        Returns:
            Deduplicated building list
        """
        seen = set()
        unique_buildings = []
        
        for building in buildings:
            # Create a unique key based on location (with some tolerance)
            key = (round(building['latitude'], 5), round(building['longitude'], 5))
            
            if key not in seen:
                seen.add(key)
                unique_buildings.append(building)
        
        return unique_buildings
    
    def _calculate_building_metrics(self, buildings: List[Dict], radius: int) -> Dict:
        """
        Calculate comprehensive building metrics for Feng Shui analysis.
        
        Args:
            buildings: List of building dictionaries
            radius: Analysis radius in meters
        
        Returns:
            Dictionary with building metrics
        """
        if not buildings:
            return {
                'total_buildings': 0,
                'avg_height': 0,
                'max_height': 0,
                'min_height': 0,
                'height_variance': 0,
                'height_stddev': 0,
                'building_density': 0,
                'dominant_height_category': 'low',
                'height_categories': {'low': 0, 'medium': 0, 'high': 0, 'very_high': 0}
            }
        
        heights = [b['height'] for b in buildings]
        
        avg_height = statistics.mean(heights)
        max_height = max(heights)
        min_height = min(heights)
        
        # Calculate variance and standard deviation
        if len(heights) > 1:
            variance = statistics.variance(heights)
            stddev = statistics.stdev(heights)
        else:
            variance = 0
            stddev = 0
        
        # Calculate building density (buildings per km²)
        area_km2 = (math.pi * (radius / 1000) ** 2)
        density = len(buildings) / area_km2 if area_km2 > 0 else 0
        
        # Categorize buildings by height
        height_categories = {
            'low': len([h for h in heights if h < 10]),        # < 10m
            'medium': len([h for h in heights if 10 <= h < 25]),  # 10-25m
            'high': len([h for h in heights if 25 <= h < 50]),    # 25-50m
            'very_high': len([h for h in heights if h >= 50])     # >= 50m (skyscrapers)
        }
        
        # Determine dominant height category
        dominant = max(height_categories, key=height_categories.get)
        
        return {
            'total_buildings': len(buildings),
            'avg_height': round(avg_height, 2),
            'max_height': round(max_height, 2),
            'min_height': round(min_height, 2),
            'height_variance': round(max_height - min_height, 2),
            'height_stddev': round(stddev, 2),
            'building_density': round(density, 2),  # buildings per km²
            'dominant_height_category': dominant,
            'height_categories': height_categories
        }
    
    def _estimate_building_height(self, poi_type: str, name: str = '') -> float:
        """
        Estimate building height based on POI type and name.
        
        Args:
            poi_type: AMap POI type code
            name: Building name (may contain height clues)
        
        Returns:
            Estimated height in meters
        """
        # Try to extract height from building name
        height_from_name = self._extract_height_from_name(name)
        if height_from_name > 0:
            return height_from_name
        
        # Default heights by building type
        type_heights = {
            '120100': 25,  # Office/Commercial - typically 5+ stories
            '120200': 20,  # Government - moderate height
            '120300': 12,  # Residential - 3-4 stories typical
            '120700': 15,  # Hospitality/Hotel
            '110300': 8,   # Industrial - usually single story
            '140300': 18,  # Cultural (museums, libraries)
            '141200': 15,  # Education (schools)
            '090000': 20,  # Medical (hospitals)
            '140800': 10,  # Religious (temples, churches)
            '150700': 12,  # Transportation stations
        }
        
        return type_heights.get(poi_type, buildings_config.AVERAGE_BUILDING_HEIGHT_M)
    
    def _extract_height_from_name(self, name: str) -> float:
        """
        Try to extract building height from the building name.
        E.g., "100-Meter Building", "30층 빌딩" (30-story), etc.
        
        Args:
            name: Building name string
        
        Returns:
            Extracted height in meters, or 0 if not found
        """
        import re
        
        if not name:
            return 0
        
        # Look for patterns like "100m", "100米", "100-meter", "30-story" etc.
        patterns = [
            r'(\d+)\s*m(?:eter|eters)?',  # 100m, 100 meter
            r'(\d+)\s*米',                  # 100米 (Chinese)
            r'(\d+)\s*(?:floor|story|층)',  # 30-story, 30floor
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                # If it's a story/floor count, multiply by ~3.5m per floor
                if 'story' in pattern or 'floor' in pattern or '층' in pattern:
                    return value * 3.5
                return float(value)
        
        return 0
    
    def _estimate_building_area(self, poi_type: str) -> float:
        """
        Estimate building footprint area in square meters.
        
        Args:
            poi_type: AMap POI type code
        
        Returns:
            Estimated footprint area in m²
        """
        type_areas = {
            '120100': 1500,  # Office - large footprint
            '120200': 1200,  # Government
            '120300': 500,   # Residential - smaller units
            '120700': 800,   # Hotel
            '110300': 2000,  # Industrial - largest
            '140300': 1000,  # Cultural
            '141200': 1200,  # Education
            '090000': 1500,  # Medical
            '140800': 400,   # Religious
            '150700': 800,   # Transportation
        }
        
        return type_areas.get(poi_type, 800)
    
    def _get_building_type_name(self, poi_type: str) -> str:
        """
        Convert POI type code to readable building type name.
        
        Args:
            poi_type: AMap POI type code
        
        Returns:
            Human-readable building type name
        """
        type_names = {
            '120100': 'Commercial',
            '120200': 'Government',
            '120300': 'Residential',
            '120700': 'Hospitality',
            '110300': 'Industrial',
            '140300': 'Cultural',
            '141200': 'Education',
            '090000': 'Medical',
            '140800': 'Religious',
            '150700': 'Transportation',
        }
        
        return type_names.get(poi_type, 'Mixed-Use')
    
    def _calculate_distance(self, 
                           lon1: float, lat1: float,
                           lon2: float, lat2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Args:
            lon1, lat1: First point (longitude, latitude)
            lon2, lat2: Second point (longitude, latitude)
        
        Returns:
            Distance in meters
        """
        R = 6371000  # Earth radius in meters
        
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        
        a = (math.sin(dLat / 2) * math.sin(dLat / 2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dLon / 2) * math.sin(dLon / 2))
        
        c = 2 * math.asin(math.sqrt(a))
        distance = R * c
        
        return distance
    
    def calculate_building_harmony_score(self, metrics: Dict) -> float:
        """
        Calculate Feng Shui building harmony score based on metrics.
        
        In Feng Shui:
        - Balanced heights (lower variance) = better harmony
        - Moderate density (not too crowded) = better Qi flow
        - Mix of heights (not all same) = visual interest and balance
        
        Args:
            metrics: Building metrics dictionary from get_building_data()
        
        Returns:
            Harmony score (0-1, where 1 is perfect harmony)
        """
        if metrics['total_buildings'] == 0:
            return 0.5  # Neutral for empty area
        
        score = 0.5  # Start at neutral
        
        # Factor 1: Height variance (moderate is best)
        variance = metrics['height_variance']
        if 5 <= variance <= 40:
            # Ideal range: some variation but not extreme
            score += 0.2
        elif variance > 40:
            # Too much variation - chaotic
            score -= 0.1
        else:
            # Too uniform - monotonous
            score -= 0.05
        
        # Factor 2: Building density
        density = metrics['building_density']
        if density < 50:
            # Too sparse - dead area
            score -= 0.1
        elif 50 <= density <= 250:
            # Ideal density - balanced
            score += 0.15
        else:
            # Too crowded - suffocating
            score -= 0.15
        
        # Factor 3: Height distribution diversity
        categories = metrics['height_categories']
        non_zero = sum(1 for v in categories.values() if v > 0)
        
        if non_zero >= 3:
            # Multiple height categories = balance
            score += 0.15
        elif non_zero == 2:
            # Some diversity
            score += 0.05
        # else: only one category = less balanced
        
        # Clamp to 0-1
        return max(0, min(1, score))


# Create singleton instance
buildings_service = BuildingsService()
