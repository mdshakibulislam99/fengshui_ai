# Demo Mode Service - Simulates AMap API responses for testing

import logging
import math
import random
from typing import Dict, List

logger = logging.getLogger(__name__)

def simulate_pois_based_on_location(longitude: float, latitude: float, radius: int) -> Dict[str, List[Dict]]:
    """
    Generate realistic simulated POI data based on location coordinates.
    Different locations will have different characteristics.
    
    Args:
        longitude: Longitude of center point
        latitude: Latitude of center point  
        radius: Search radius in meters
    
    Returns:
        Dictionary with simulated categorized POI data
    """
    logger.info(f"[DEMO MODE] Simulating POIs for ({longitude}, {latitude})")
    
    # Use coordinates to seed random but consistent results for each location
    seed = int((longitude + latitude) * 10000)
    random.seed(seed)
    
    # Determine location characteristics based on coordinates
    # This makes different areas have different "personalities"
    
    # Distance from Beijing center (116.397428, 39.90923)
    dist_from_center = math.sqrt((longitude - 116.397428)**2 + (latitude - 39.90923)**2)
    
    # Suburban factor (higher = more suburban/park-like)
    suburban_factor = min(dist_from_center * 50, 1.0)
    
    # Urban density (higher near city center)
    urban_density = max(0, 1.0 - dist_from_center * 30)
    
    # Generate parks (more in suburban areas and specific park zones)
    parks = []
    # Check if near known park coordinates
    near_olympic_park = abs(longitude - 116.388) < 0.01 and abs(latitude - 40.002) < 0.01
    near_chaoyang_park = abs(longitude - 116.477) < 0.01 and abs(latitude - 39.928) < 0.01
    
    if near_olympic_park:
        park_count = random.randint(3, 5)
    elif near_chaoyang_park:
        park_count = random.randint(2, 4)
    elif suburban_factor > 0.5:
        park_count = random.randint(1, 3)
    elif urban_density < 0.3:
        park_count = random.randint(0, 2)
    else:
        park_count = 0
    
    for i in range(park_count):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(50, radius * 0.9)
        parks.append({
            'name': f'Park {i+1}',
            'longitude': longitude + dist * math.cos(angle) / 111320,
            'latitude': latitude + dist * math.sin(angle) / 110540,
            'distance': dist
        })
    
    # Generate water bodies (more near specific areas)
    water = []
    near_houhai = abs(longitude - 116.383) < 0.01 and abs(latitude - 39.937) < 0.01
    near_water = near_olympic_park or near_houhai
    
    if near_water:
        water_count = random.randint(1, 2)
    elif suburban_factor > 0.6:
        water_count = random.randint(0, 1)
    else:
        water_count = 0
    
    for i in range(water_count):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(100, radius * 0.8)
        water.append({
            'name': f'Water Body {i+1}',
            'longitude': longitude + dist * math.cos(angle) / 111320,
            'latitude': latitude + dist * math.sin(angle) / 110540,
            'distance': dist
        })
    
    # Buildings (more in urban areas)
    building_count = int(20 + urban_density * 100 + random.randint(-10, 10))
    buildings = []
    for i in range(building_count):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(10, radius * 0.95)
        buildings.append({
            'name': f'Building {i+1}',
            'longitude': longitude + dist * math.cos(angle) / 111320,
            'latitude': latitude + dist * math.sin(angle) / 110540,
            'distance': dist
        })
    
    # Residential (moderate in all areas)
    residential_count = int(10 + random.randint(0, 30))
    residential = []
    for i in range(residential_count):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(50, radius * 0.9)
        residential.append({
            'name': f'Residential {i+1}',
            'longitude': longitude + dist * math.cos(angle) / 111320,
            'latitude': latitude + dist * math.sin(angle) / 110540,
            'distance': dist
        })
    
    # Transportation (more in urban, near roads)
    transport_count = int(urban_density * 8 + random.randint(0, 5))
    transportation = []
    for i in range(transport_count):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(100, radius)
        transportation.append({
            'name': f'Transport {i+1}',
            'longitude': longitude + dist * math.cos(angle) / 111320,
            'latitude': latitude + dist * math.sin(angle) / 110540,
            'distance': dist
        })
    
    # Hospitals (1-2 per area)
    hospital_count = random.randint(0, 2) if urban_density > 0.3 else 0
    hospitals = []
    for i in range(hospital_count):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(200, radius)
        hospitals.append({
            'name': f'Hospital {i+1}',
            'longitude': longitude + dist * math.cos(angle) / 111320,
            'latitude': latitude + dist * math.sin(angle) / 110540,
            'distance': dist
        })
    
    # Schools (2-4 in populated areas)
    school_count = random.randint(1, 4) if urban_density > 0.2 or suburban_factor > 0.4 else 0
    schools = []
    for i in range(school_count):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(150, radius)
        schools.append({
            'name': f'School {i+1}',
            'longitude': longitude + dist * math.cos(angle) / 111320,
            'latitude': latitude + dist * math.sin(angle) / 110540,
            'distance': dist
        })
    
    # Temples (occasional)
    temple_count = random.randint(0, 1) if random.random() > 0.7 else 0
    temples = []
    for i in range(temple_count):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(200, radius)
        temples.append({
            'name': f'Temple {i+1}',
            'longitude': longitude + dist * math.cos(angle) / 111320,
            'latitude': latitude + dist * math.sin(angle) / 110540,
            'distance': dist
        })
    
    logger.info(f"[DEMO] Generated: {park_count} parks, {water_count} water, {building_count} buildings")
    
    return {
        'parks': parks,
        'water': water,
        'buildings': buildings,
        'residential': residential,
        'transportation': transportation,
        'hospitals': hospitals,
        'schools': schools,
        'temples': temples
    }


def simulate_road_network(longitude: float, latitude: float, radius: int) -> Dict:
    """
    Generate simulated road network data.
    
    Returns:
        Dictionary with roads and intersections
    """
    seed = int((longitude + latitude) * 10000)
    random.seed(seed)
    
    # Distance from center determines road density
    dist_from_center = math.sqrt((longitude - 116.397428)**2 + (latitude - 39.90923)**2)
    urban_density = max(0, 1.0 - dist_from_center * 30)
    
    # More roads and intersections in urban areas
    road_count = int(5 + urban_density * 15 + random.randint(0, 5))
    intersection_count = int(3 + urban_density * 17 + random.randint(0, 8))
    
    roads = []
    for i in range(road_count):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(50, radius * 0.8)
        roads.append({
            'name': f'Road {i+1}',
            'longitude': longitude + dist * math.cos(angle) / 111320,
            'latitude': latitude + dist * math.sin(angle) / 110540
        })
    
    intersections = []
    for i in range(intersection_count):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(50, radius * 0.9)
        intersections.append({
            'name': f'Intersection {i+1}',
            'longitude': longitude + dist * math.cos(angle) / 111320,
            'latitude': latitude + dist * math.sin(angle) / 110540
        })
    
    logger.info(f"[DEMO] Generated: {road_count} roads, {intersection_count} intersections")
    
    return {
        'roads': roads,
        'intersections': intersections,
        'road_count': road_count
    }
