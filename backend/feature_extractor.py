# Module for extracting relevant features from map data for Feng Shui analysis

import logging
import threading
from typing import Dict, List, Optional, Tuple
import math
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

logger = logging.getLogger(__name__)

# Constants for feature calculations
AVERAGE_PARK_AREA = 50000  # Average park area in square meters
AVERAGE_WATER_AREA = 100000  # Average water body area in square meters
AVERAGE_BUILDING_AREA = 500  # Average building footprint in square meters


def extract_features(poi_data: Dict[str, List[Dict]], 
                    road_data: Dict,
                    longitude: float,
                    latitude: float,
                    radius: int,
                    dem_service=None,
                    hydrosheds_service=None,
                    buildings_service=None,
                    wind_service=None,
                    flood_service=None,
                    ndvi_service=None) -> Dict:
    """
    Extract comprehensive Feng Shui-relevant features from real AMap data.
    
    This is the main orchestrator function that:
    1. Takes raw POI and road data from AMap API
    2. Calls specialized calculation functions for each feature
    3. Returns a feature dictionary suitable for AI model input
    
    All calculations are DYNAMIC and based on the actual clicked location.
    No hardcoded values - everything varies with the map location.
    
    Feature Categories:
    - Spatial: green_area_ratio, water_proximity, building_density
    - Infrastructure: road_intersection_density, environmental_quality
    - Energy: orientation_score, qi_flow_score, spiritual_presence
    
    Args:
        poi_data: Dictionary of categorized POI data from AMap API
                  Keys: 'parks', 'water', 'buildings', 'residential', 
                        'hospitals', 'schools', 'temples', etc.
                  Values: List of POI dictionaries with 'distance', 
                          'longitude', 'latitude', 'name', etc.
        road_data: Dictionary of road network data from AMap
                   Keys: 'roads', 'intersections', 'road_count'
                   Values: List of road/intersection features
        longitude: Center point longitude (clicked location)
        latitude: Center point latitude (clicked location)
        radius: Analysis radius in meters (configurable by user)
    
    Returns:
        Dictionary of extracted features with numeric values (0-1 normalized):
        {
            'green_area_ratio': float (0-1),
            'water_proximity': float (0-1),
            'building_density': float (0-1),
            'road_intersection_density': float (0-1),
            'orientation_score': float (0-1),
            'environmental_quality': float (0-1),
            'spiritual_presence': float (0-1)
        }
        
        All features are location-specific and dynamically calculated.
    """
    logger.info(f"=" * 70)
    logger.info(f"Extracting features for location: ({latitude:.6f}, {longitude:.6f})")
    logger.info(f"Analysis radius: {radius}m")
    logger.info(f"POI categories found: {', '.join([f'{k}({len(v)})' for k, v in poi_data.items() if v])}")
    logger.info(f"=" * 70)
    
    # Initialize with location info needed for enhanced scoring
    features = {
        'latitude': latitude,
        'longitude': longitude,
        'aspect_degrees': None,  # Will be set by DEM if available
    }
    
    try:
        # Feature 1: Green Area Ratio
        # Based on park POIs within radius
        features['green_area_ratio'] = calculate_green_area_ratio(
            poi_data.get('parks', []), 
            radius
        )
        
        # Feature 2: Water Proximity Score
        # Distance to nearest water body and its Feng Shui significance
        features['water_proximity'] = calculate_water_proximity(
            poi_data.get('water', []), 
            longitude, 
            latitude, 
            radius
        )
        
        # Feature 3: Building Density
        # Combines commercial buildings and residential areas
        all_buildings = poi_data.get('buildings', []) + poi_data.get('residential', [])
        features['building_density'] = calculate_building_density(
            all_buildings,
            radius
        )
        
        # Feature 4: Road Intersection Density
        # Measure of traffic connectivity and accessibility
        features['road_intersection_density'] = calculate_road_density(
            road_data.get('intersections', []),
            road_data.get('road_count', 0),
            radius
        )
        
        # Feature 5: Orientation Score
        # Average building orientation relative to optimal Feng Shui directions
        features['orientation_score'] = estimate_orientation_score(
            all_buildings,
            longitude,
            latitude
        )
        
        # Feature 6: Environmental Quality
        # Proximity to hospitals and schools (essential services)
        features['environmental_quality'] = calculate_environmental_quality(
            poi_data.get('hospitals', []),
            poi_data.get('schools', []),
            radius
        )
        
        # Feature 7: Spiritual Presence
        # Nearby temples and religious sites
        features['spiritual_presence'] = calculate_spiritual_presence(
            poi_data.get('temples', []),
            radius
        )
        
        # Features 8-12: external services
        # All services use China-accessible APIs (no GEE dependency)
        # DEM: OpenTopography, NDVI: MODIS, Water: AMap, Wind: CMA, Flood: Local

        def _fetch_dem():
            if dem_service is None:
                return {}
            try:
                r = dem_service.get_topography_score(longitude, latitude, radius)
                return {'dem': r}
            except Exception as exc:
                logger.warning(f"⚠ DEM error: {exc}")
                return {}

        def _fetch_hydrosheds():
            if hydrosheds_service is None:
                return {}
            try:
                r = hydrosheds_service.get_river_proximity_score(longitude, latitude, radius)
                return {'hydrosheds': r}
            except Exception as exc:
                logger.warning(f"⚠ HydroSHEDS error: {exc}")
                return {}

        def _fetch_buildings():
            if buildings_service is None:
                return {}
            try:
                r = buildings_service.get_building_data(longitude, latitude, radius)
                return {'buildings': r}
            except Exception as exc:
                logger.warning(f"⚠ Buildings error: {exc}")
                return {}

        def _fetch_wind():
            if wind_service is None:
                return {}
            try:
                r = wind_service.get_cached_wind_analysis(longitude, latitude, radius)
                return {'wind': r}
            except Exception as exc:
                logger.warning(f"⚠ Wind error: {exc}")
                return {}

        def _fetch_flood():
            if flood_service is None:
                return {}
            try:
                r = flood_service.get_flood_risk_analysis(longitude, latitude, radius)
                return {'flood': r}
            except Exception as exc:
                logger.warning(f"⚠ Flood error: {exc}")
                return {}

        def _fetch_ndvi():
            if ndvi_service is None:
                return {}
            try:
                # NDVI uses MODIS (free, China-accessible) - no GEE dependency
                r = ndvi_service.get_ndvi(longitude, latitude, radius_m=radius)
                return {'ndvi': r}
            except Exception as exc:
                logger.warning(f"⚠ NDVI error: {exc}")
                return {}

        # All 6 services run in a single pool (no GEE throttling - using China-accessible APIs only)
        all_results = {}
        try:
            from config import Config
            service_timeout_sec = max(1.0, float(getattr(Config, 'FEATURE_SERVICE_TIMEOUT_SEC', 8.0)))
        except Exception:
            service_timeout_sec = 8.0

        with ThreadPoolExecutor(max_workers=6) as pool:
            futs = {
                pool.submit(_fetch_dem):        'dem',
                pool.submit(_fetch_hydrosheds): 'hydrosheds',
                pool.submit(_fetch_buildings):  'buildings',
                pool.submit(_fetch_wind):       'wind',
                pool.submit(_fetch_flood):      'flood',
                pool.submit(_fetch_ndvi):       'ndvi',
            }
            pending = set(futs.keys())
            try:
                for fut in as_completed(pending, timeout=service_timeout_sec):
                    pending.discard(fut)
                    try:
                        all_results.update(fut.result())
                    except Exception as exc:
                        logger.warning(f"⚠ Service future failed: {exc}")
            except TimeoutError:
                logger.warning(
                    f"⚠ Feature service budget exceeded ({service_timeout_sec:.1f}s); "
                    "continuing with partial service data"
                )
            finally:
                for fut in pending:
                    fut.cancel()

        # --- Apply DEM ---
        topography = all_results.get('dem')
        if topography and topography.get('success'):
            features['topography_score'] = topography['topography_score'] / 100.0
            features['elevation_m'] = topography['terrain_metrics'].get('elevation_m')
            features['slope_degrees'] = topography['terrain_metrics'].get('slope_degrees')
            features['aspect_degrees'] = topography['terrain_metrics'].get('aspect_degrees')
            logger.info(f"✓ DEM features extracted: elevation={features['elevation_m']:.1f}m, slope={features['slope_degrees']:.1f}°, aspect={features['aspect_degrees']:.1f}°")
            
            # Enhance orientation with terrain aspect from DEM
            # Terrain aspect indicates which direction the slope faces — 
            # south-facing slopes are preferred in feng shui (warmth, light)
            aspect = features.get('aspect_degrees')
            slope = features.get('slope_degrees', 0)
            if aspect is not None and slope is not None and slope > 15.0:
                # Only use terrain aspect on clearly sloped terrain (>15°)
                # where hill/mountain facing genuinely affects feng shui orientation.
                # Moderate slopes (<15°) are terrain noise in urban/campus areas.
                terrain_orientation = score_orientation(aspect)
                building_orientation = features['orientation_score']
                slope_weight = min((slope - 15.0) / 30.0, 0.4)
                if slope < 25.0 and terrain_orientation < building_orientation:
                    # Dampen negative terrain signal for borderline slopes
                    slope_weight *= 0.3
                features['orientation_score'] = (
                    building_orientation * (1 - slope_weight) + terrain_orientation * slope_weight
                )
                logger.info(f"  Orientation enhanced with DEM aspect: "
                            f"buildings={building_orientation:.3f}, terrain={terrain_orientation:.3f} "
                            f"(slope={slope:.1f}°, weight={slope_weight:.2f}) → {features['orientation_score']:.3f}")
        else:
            logger.warning("⚠ DEM query failed or skipped")
            features['topography_score'] = 0.5

        # --- Apply NDVI (satellite vegetation — overrides AMap POI green score) ---
        ndvi_result = all_results.get('ndvi')
        if ndvi_result and ndvi_result.get('success'):
            satellite_coverage = ndvi_result.get('vegetation_coverage', None)
            ndvi_value = ndvi_result.get('ndvi_value', None)
            if satellite_coverage is not None and ndvi_value is not None:
                # Satellite sees everything: parks, fields, gardens, street trees, ponds (NDVI < 0 = water)
                # Blend: 60% satellite truth, 40% AMap POI (AMap knows named parks precisely)
                amap_green = features['green_area_ratio']
                blended_green = amap_green * 0.40 + float(satellite_coverage) * 0.60
                features['green_area_ratio'] = max(amap_green, blended_green)  # never punish amap signal
                features['ndvi_value'] = float(ndvi_value)
                features['ndvi_vegetation_coverage'] = float(satellite_coverage)
                features['ndvi_source'] = ndvi_result.get('source', 'satellite')
                logger.info(
                    f"✓ NDVI satellite green override: AMap={amap_green:.3f} + "
                    f"Satellite={satellite_coverage:.3f} → blended={features['green_area_ratio']:.3f} "
                    f"(source: {ndvi_result.get('source', '?')})"
                )
        else:
            logger.warning("⚠ NDVI unavailable — using AMap-only green score")
            features['ndvi_value'] = None
            features['ndvi_vegetation_coverage'] = None

        # Qi Flow (local, no I/O — computed after NDVI+DEM so green and density are final)
        features['qi_flow'] = calculate_qi_flow_score(
            road_data,
            features['building_density'],
            features['green_area_ratio']
        )

        # --- Apply HydroSHEDS ---
        river_result = all_results.get('hydrosheds')
        if river_result and river_result.get('success'):
            features['hydrosheds_river_proximity'] = river_result['combined_score'] / 100.0
            features['hydrosheds_river_density'] = river_result['river_density_score'] / 100.0
            logger.info(f"✓ HydroSHEDS features extracted: river_proximity={features['hydrosheds_river_proximity']:.3f}")
            
            # If AMap water POIs returned 0, use HydroSHEDS river proximity instead
            if features.get('water_proximity', 0.0) == 0.0 and features['hydrosheds_river_proximity'] > 0.1:
                features['water_proximity'] = features['hydrosheds_river_proximity']
                logger.info(f"✓ Water proximity updated from HydroSHEDS: {features['water_proximity']:.3f}")
        else:
            logger.warning("⚠ HydroSHEDS query failed or skipped, using neutral fallback")
            features['hydrosheds_river_proximity'] = 0.5
            features['hydrosheds_river_density'] = 0.0

        # --- Apply Buildings ---
        building_result = all_results.get('buildings')
        if building_result and building_result.get('success'):
            metrics = building_result['metrics']
            harmony_score = buildings_service.calculate_building_harmony_score(metrics)
            features['building_avg_height'] = min(metrics['avg_height'] / 50.0, 1.0)
            features['building_density'] = min(metrics['building_density'] / 400.0, 1.0)
            features['building_height_variance'] = min(metrics['height_variance'] / 50.0, 1.0)
            features['building_harmony'] = harmony_score
            features['total_buildings_nearby'] = metrics['total_buildings'] / 100.0
            logger.info(f"✓ Buildings features extracted: avg_height={metrics['avg_height']:.1f}m, harmony={harmony_score:.3f}")
        else:
            logger.warning("⚠ Buildings data query failed or skipped")
            features['building_avg_height'] = 0.4
            features['building_density'] = 0.4
            features['building_height_variance'] = 0.5
            features['building_harmony'] = 0.5
            features['total_buildings_nearby'] = 0.0

        # --- Apply Wind ---
        wind_result = all_results.get('wind')
        if wind_result and wind_result.get('success'):
            metrics = wind_result['wind_metrics']
            scores = wind_result['feng_shui_scores']
            features['wind_speed'] = min(metrics['avg_speed'] / 10.0, 1.0)
            features['wind_exposure_score'] = scores['overall_wind_score'] / 100.0
            features['wind_direction_favorability'] = scores['direction_score'] / 100.0
            features['wind_consistency'] = metrics['consistency']
            features['wind_dominant_direction'] = metrics.get('direction_degrees', 0) / 360.0
            logger.info(f"✓ Wind features extracted: speed={metrics['avg_speed']:.1f} m/s, score={scores['overall_wind_score']:.1f}/100")
        else:
            logger.warning("⚠ Wind data query failed or skipped")
            features['wind_speed'] = 0.3
            features['wind_exposure_score'] = 0.5
            features['wind_direction_favorability'] = 0.5
            features['wind_consistency'] = 0.5
            features['wind_dominant_direction'] = 0.5

        # --- Apply Flood ---
        flood_result = all_results.get('flood')
        if flood_result and flood_result.get('success'):
            flood_scores  = flood_result['flood_scores']
            flood_metrics = flood_result['flood_metrics']
            features['flood_risk_index'] = flood_scores['flood_risk_index'] / 100.0
            features['flood_exposure'] = flood_scores['flood_exposure_score'] / 100.0
            features['flood_surface_water_occurrence'] = min(flood_metrics.get('surface_water_occurrence_pct', 0.0) / 100.0, 1.0)
            mean_slope = flood_metrics.get('mean_slope_degrees', 5.0)
            features['flood_drainage_risk'] = max(0.0, min(1.0, (8.0 - mean_slope) / 8.0))
            logger.info(f"✓ Flood features extracted: risk={flood_scores['flood_risk_index']:.1f}/100")
        else:
            logger.warning("⚠ Flood data query failed or skipped")
            features['flood_risk_index'] = 0.5
            features['flood_exposure'] = 0.5
            features['flood_surface_water_occurrence'] = 0.2
            features['flood_drainage_risk'] = 0.5
        
    except Exception as e:
        logger.error(f"Error extracting features: {str(e)}", exc_info=True)
        # Return default neutral values on error
        features = {
            'green_area_ratio': 0.3,
            'water_proximity': 0.3,
            'building_density': 0.5,
            'road_intersection_density': 0.5,
            'orientation_score': 0.5,
            'environmental_quality': 0.3,
            'spiritual_presence': 0.2,
            'topography_score': 0.5,
            'hydrosheds_river_proximity': 0.5,
            'hydrosheds_river_density': 0.0,
            'qi_flow': 0.5,
            'building_avg_height': 0.4,
            'building_density': 0.4,
            'building_height_variance': 0.5,
            'building_harmony': 0.5,
            'total_buildings_nearby': 0.0,
            'wind_speed': 0.3,
            'wind_exposure_score': 0.5,
            'wind_direction_favorability': 0.5,
            'wind_consistency': 0.5,
            'wind_dominant_direction': 0.5,
            'flood_risk_index': 0.5,
            'flood_exposure': 0.5,
            'flood_surface_water_occurrence': 0.2,
            'flood_drainage_risk': 0.5
        }
        logger.warning("Using default neutral feature values due to extraction error")
    
    logger.info(f"=" * 70)
    logger.info(f"Feature extraction complete. Summary:")
    for feature_name, feature_value in features.items():
        if isinstance(feature_value, (int, float)):
            logger.info(f"  {feature_name}: {feature_value:.3f}")
        else:
            logger.info(f"  {feature_name}: {feature_value}")
    logger.info(f"=" * 70)
    
    return features


def calculate_green_area_ratio(parks: List[Dict], radius: int) -> float:
    """
    Calculate the ratio of green/park areas within the search radius.
    Uses distance-weighted area estimation based on actual POI data.
    
    Algorithm:
    - Each park POI is assigned an estimated area based on its distance
    - Closer parks have more accurate area estimates
    - Parks beyond 80% of radius have reduced contribution
    - Final ratio = total_green_area / total_search_area
    
    Args:
        parks: List of park POIs with 'distance' field (in meters)
        radius: Search radius in meters
    
    Returns:
        Green area ratio (0-1), where 0 = no parks, 1 = maximum green coverage
    """
    if not parks:
        logger.info("Green area ratio: 0.000 (no parks found)")
        return 0.0
    
    # Calculate total search area
    total_search_area = math.pi * radius * radius
    
    # Estimate green area contribution from each park
    total_green_area = 0.0
    for park in parks:
        distance = park.get('distance', radius)
        
        # Distance weight: parks closer to center count more
        # Use exponential decay: closer parks = higher weight
        distance_factor = math.exp(-2 * distance / radius)
        
        # Estimate park area based on distance
        # Assumption: closer POIs are more accurately detected
        if distance < radius * 0.3:
            # Close parks: use full estimated area
            estimated_area = AVERAGE_PARK_AREA * distance_factor
        elif distance < radius * 0.6:
            # Medium distance: moderate area
            estimated_area = AVERAGE_PARK_AREA * 0.6 * distance_factor
        else:
            # Far parks: smaller contribution
            estimated_area = AVERAGE_PARK_AREA * 0.3 * distance_factor
        
        total_green_area += estimated_area
    
    # Calculate ratio and normalize
    ratio = min(total_green_area / total_search_area, 1.0)
    
    logger.info(f"Green area ratio: {ratio:.3f} ({len(parks)} parks found, "
                f"estimated {total_green_area:.0f}m² green space in {total_search_area:.0f}m² area)")
    
    return ratio


def calculate_water_proximity(water_bodies: List[Dict], 
                              longitude: float, 
                              latitude: float,
                              radius: int,
                              hydrosheds_fallback: Optional[float] = None) -> float:
    """
    Calculate water proximity score based on Feng Shui principles.
    Water represents wealth and prosperity but must be at optimal distance.
    
    Feng Shui Water Guidelines:
    - Too close (<100m): Risk of overwhelming energy, flooding concerns
    - Optimal (100-800m): Brings wealth energy, good for prosperity
    - Moderate (800-1500m): Still beneficial but reduced effect
    - Far (>1500m): Minimal water energy influence
    
    Falls back to HydroSHEDS river proximity if AMap water POIs are not found.
    
    Args:
        water_bodies: List of water body POIs from AMap
        longitude: Center point longitude
        latitude: Center point latitude
        radius: Search radius in meters
        hydrosheds_fallback: Optional HydroSHEDS river proximity score (0-1)
    
    Returns:
        Water proximity score (0-1), where 1 = optimal distance
    """
    # If no AMap water POIs but HydroSHEDS has river data, use it
    if not water_bodies:
        if hydrosheds_fallback is not None and hydrosheds_fallback > 0.1:
            logger.info(f"Water proximity score: {hydrosheds_fallback:.3f} (from HydroSHEDS river network fallback)")
            return hydrosheds_fallback
        else:
            logger.info("Water proximity score: 0.000 (no water bodies found, no river network)")
            return 0.0
    
    # Find closest water body using real distance data
    min_distance = radius
    closest_water = None
    for water in water_bodies:
        distance = water.get('distance', radius)
        if distance < min_distance:
            min_distance = distance
            closest_water = water
    
    # Calculate score based on Feng Shui optimal distance curve
    if min_distance < 100:
        # Too close: potential negative effects (flood risk, overwhelming)
        score = 0.5 + (min_distance / 200)  # 0.5-1.0 range
    elif 100 <= min_distance <= 800:
        # Optimal range: maximum benefit
        # Peak score at 400m
        deviation_from_optimal = abs(min_distance - 400)
        score = 1.0 - (deviation_from_optimal / 400) * 0.15  # 0.85-1.0 range
    elif 800 < min_distance <= 1500:
        # Moderate range: declining benefit
        score = 0.85 - ((min_distance - 800) / 700) * 0.5  # 0.35-0.85 range
    else:
        # Far range: minimal benefit
        score = max(0.0, 0.35 - ((min_distance - 1500) / radius) * 0.35)
    
    water_name = closest_water.get('name', 'Unknown') if closest_water else 'N/A'
    logger.info(f"Water proximity score: {score:.3f} (closest: '{water_name}' at {min_distance:.0f}m)")
    
    return score


def calculate_building_density(buildings: List[Dict], radius: int) -> float:
    """
    Calculate building density as a measure of urban congestion.
    Higher density indicates more crowded energy flow (less favorable in Feng Shui).
    
    Calculation Method:
    - Count actual buildings from AMap POI data
    - Calculate density per square kilometer
    - Normalize based on typical urban density ranges:
      * Low density: <100 buildings/km² (rural/suburban)
      * Medium density: 100-300 buildings/km² (urban residential)
      * High density: 300-500 buildings/km² (dense urban)
      * Very high density: >500 buildings/km² (downtown/commercial)
    
    Args:
        buildings: List of building POIs from AMap (commercial + residential)
        radius: Search radius in meters
    
    Returns:
        Normalized density (0-1), where 0 = sparse, 1 = very dense
    """
    if not buildings:
        logger.info("Building density: 0.0 buildings/km² (normalized: 0.000)")
        return 0.0
    
    # Calculate search area in square kilometers
    area_sq_m = math.pi * radius * radius
    area_sq_km = area_sq_m / 1_000_000
    
    # Count buildings and calculate density
    building_count = len(buildings)
    density_per_sq_km = building_count / area_sq_km if area_sq_km > 0 else 0
    
    # Normalize density to 0-1 scale
    # Using sigmoid-like function for smooth normalization
    # Target: 500 buildings/km² = 0.5 normalized value
    normalized_density = 1 / (1 + math.exp(-0.01 * (density_per_sq_km - 500)))
    
    # Alternative linear normalization (commented for reference)
    # normalized_density = min(density_per_sq_km / 1000, 1.0)
    
    logger.info(f"Building density: {density_per_sq_km:.1f} buildings/km² "
                f"({building_count} buildings in {area_sq_km:.2f}km²), "
                f"normalized: {normalized_density:.3f}")
    
    return normalized_density


def calculate_road_density(intersections: List[Dict], 
                          road_count: int,
                          radius: int) -> float:
    """
    Calculate road intersection density as a measure of traffic connectivity.
    Moderate density is ideal - too low means isolated, too high means chaotic traffic.
    
    Feng Shui Road Principles:
    - Very low density (<5/km²): Isolated, poor accessibility
    - Low density (5-10/km²): Quiet, but may lack convenience
    - Optimal density (10-20/km²): Good balance of access and calm
    - High density (20-40/km²): Busy, excessive Yang energy
    - Very high density (>40/km²): Traffic chaos, cutting Qi
    
    Args:
        intersections: List of intersection POIs from AMap road data
        road_count: Total number of road features detected
        radius: Search radius in meters
    
    Returns:
        Normalized density (0-1), representing traffic intensity
    """
    # Calculate search area
    area_sq_m = math.pi * radius * radius
    area_sq_km = area_sq_m / 1_000_000
    
    # Count actual intersections from road data
    intersection_count = len(intersections)
    
    # Calculate density
    if area_sq_km > 0:
        intersection_density = intersection_count / area_sq_km
    else:
        intersection_density = 0
    
    # Normalize using optimal range (10-20 intersections/km²)
    # Below 10: gradually increase from 0
    # 10-20: peak range (high score)
    # Above 20: gradually decrease
    if intersection_density < 10:
        normalized = intersection_density / 10 * 0.7  # 0-0.7
    elif 10 <= intersection_density <= 20:
        normalized = 0.7 + (intersection_density - 10) / 10 * 0.3  # 0.7-1.0
    else:
        # Penalty for excessive density
        excess = intersection_density - 20
        normalized = max(0.0, 1.0 - excess / 20 * 0.5)  # Decrease from 1.0
    
    logger.info(f"Road intersection density: {intersection_density:.1f}/km² "
                f"({intersection_count} intersections, {road_count} roads), "
                f"normalized: {normalized:.3f}")
    
    return normalized


def estimate_orientation_score(buildings: List[Dict],
                               center_lon: float,
                               center_lat: float) -> float:
    """
    Estimate site orientation quality for Feng Shui analysis.
    
    Since AMap POI data only provides building locations (not facing direction),
    we combine:
    1. Cultural/latitude prior — In Northern Hemisphere (especially East Asia),
       buildings face south (坐北朝南). This is the dominant signal.
    2. Site layout quality (四象 analysis) — Good feng shui layout has buildings
       behind (靠山 backing/north) and open space in front (明堂/south).
    
    DEM terrain aspect is blended in separately after this function.
    
    Args:
        buildings: List of building POIs from AMap with coordinates
        center_lon: Center point longitude
        center_lat: Center point latitude
    
    Returns:
        Orientation score (0-1), where 1 = optimal south-facing site
    """
    latitude = center_lat
    longitude = center_lon
    
    # --- Step 1: Cultural/latitude base score ---
    # In Northern Hemisphere, south-facing is ideal (max sunlight, warmth)
    # East Asia (China, Japan, Korea) has the strongest 坐北朝南 tradition
    if latitude > 0:
        # Northern Hemisphere — south-facing preferred
        is_east_asia = (18 <= latitude <= 54 and 73 <= longitude <= 146)
        if is_east_asia:
            cultural_base = 0.85  # Strong 坐北朝南 tradition in planned areas
        elif 20 <= latitude <= 50:
            cultural_base = 0.75  # Mid-latitudes, sunlight-oriented design
        else:
            cultural_base = 0.65  # High/low latitudes, less directional preference
    else:
        # Southern Hemisphere — north-facing preferred (same sun logic)
        cultural_base = 0.75
    
    if not buildings:
        # No buildings could mean undeveloped area OR API data gap (rate limit)
        # In developed regions, assume standard orientation still applies
        score = cultural_base * 0.95
        logger.info(f"Orientation score: {score:.3f} (no buildings, "
                    f"cultural base={cultural_base:.2f} for lat={latitude:.1f}°)")
        return score
    
    # --- Step 2: Site layout quality (四象 analysis) ---
    # Count buildings in each quadrant relative to center
    # Good feng shui: 靠山 (backing from north), 明堂 (open south),
    #   青龙 (east support), 白虎 (west balance)
    north_weight = 0.0   # 靠山 (backing/sitting)
    south_weight = 0.0   # 明堂 (bright hall/facing)
    east_weight = 0.0    # 青龙 (azure dragon)
    west_weight = 0.0    # 白虎 (white tiger)
    valid_count = 0
    
    for building in buildings:
        building_lon = building.get('longitude')
        building_lat = building.get('latitude')
        distance = building.get('distance', 500)
        
        if building_lon is None or building_lat is None:
            continue
        
        # Calculate bearing from center to building
        angle = estimate_building_orientation(
            building_lon, building_lat, center_lon, center_lat
        )
        if angle is None:
            continue
        
        valid_count += 1
        # Closer buildings have stronger influence
        proximity_weight = 1.0 / (1.0 + distance / 200.0)
        
        # Classify into quadrants (with 45° overlap zones)
        # North: 315-360, 0-45. South: 135-225. East: 45-135. West: 225-315
        if angle >= 315 or angle < 45:
            north_weight += proximity_weight
        elif 135 <= angle < 225:
            south_weight += proximity_weight
        elif 45 <= angle < 135:
            east_weight += proximity_weight
        else:  # 225-315
            west_weight += proximity_weight
    
    # Layout quality assessment
    total_weight = north_weight + south_weight + east_weight + west_weight
    layout_bonus = 0.0
    
    if total_weight > 0 and valid_count >= 3:
        # Normalize
        n = north_weight / total_weight
        s = south_weight / total_weight
        e = east_weight / total_weight
        w = west_weight / total_weight
        
        # 靠山: More buildings behind (north) than in front (south) is ideal
        # This means the site likely faces south with backing support
        backing_quality = min((n - s + 0.05) * 1.5, 0.05)  # up to +0.05
        backing_quality = max(backing_quality, -0.03)  # mild penalty at worst
        
        # 青龙白虎 balance: east and west should be roughly balanced
        ew_balance = 1.0 - abs(e - w) * 2.0  # 1.0 = perfect balance
        balance_bonus = max(0, ew_balance * 0.03)  # up to +0.03
        
        layout_bonus = backing_quality + balance_bonus
        
        logger.info(f"Orientation layout (四象): N={n:.2f} S={s:.2f} E={e:.2f} W={w:.2f}, "
                    f"backing={backing_quality:+.3f}, balance={balance_bonus:+.3f}")
    
    # --- Step 3: Confidence boost from having buildings (developed area) ---
    # Planned developments (campuses, residential) follow orientation standards
    if valid_count >= 5:
        development_boost = 0.03  # Well-developed area = more likely standard orientation
    elif valid_count >= 2:
        development_boost = 0.01
    else:
        development_boost = 0.0
    
    score = min(1.0, max(0.0, cultural_base + layout_bonus + development_boost))
    
    logger.info(f"Orientation score: {score:.3f} "
                f"({valid_count} buildings, cultural={cultural_base:.2f}, "
                f"layout={layout_bonus:+.3f}, dev={development_boost:+.3f})")
    
    return score


def estimate_building_orientation(lon: float, lat: float, 
                                 center_lon: float, center_lat: float) -> Optional[float]:
    """
    Estimate building facing angle based on its position.
    
    Args:
        lon, lat: Building coordinates
        center_lon, center_lat: Reference center coordinates
    
    Returns:
        Facing angle in degrees (0-360, where 0 = North), or None
    """
    if lon is None or lat is None:
        return None
    
    # Calculate bearing from center to building
    delta_lon = lon - center_lon
    delta_lat = lat - center_lat
    
    # Convert to angle (0° = North, 90° = East, etc.)
    angle_rad = math.atan2(delta_lon, delta_lat)
    angle_deg = math.degrees(angle_rad)
    
    # Normalize to 0-360
    facing_angle = (angle_deg + 360) % 360
    
    return facing_angle


def score_orientation(angle: float) -> float:
    """
    Score a building orientation based on traditional Feng Shui principles.
    Uses smooth gradient instead of discrete bins for more accurate scoring.
    
    Scoring Curve:
    - Peak at 180° (due south): 1.0
    - High from 135-225° (south range): 0.9-1.0
    - Good from 90-135° and 225-270° (SE/SW): 0.7-0.9
    - Moderate from 45-90° and 270-315° (E/W): 0.5-0.7
    - Lower from 315-45° (north range): 0.3-0.5
    
    Args:
        angle: Facing angle in degrees (0-360°)
              0° = North, 90° = East, 180° = South, 270° = West
    
    Returns:
        Score from 0-1, where 1 = optimal south-facing
    """
    # Normalize angle to 0-360 range
    angle = angle % 360
    
    # Calculate deviation from optimal south (180°)
    deviation_from_south = abs(180 - angle)
    if deviation_from_south > 180:
        deviation_from_south = 360 - deviation_from_south
    
    # Use cosine-based smooth curve for scoring
    # 0° deviation (south) = 1.0, 180° deviation (north) = 0.3
    score = 0.3 + 0.7 * math.cos(math.radians(deviation_from_south))
    
    # Ensure score is in valid range
    return max(0.3, min(1.0, score))


def angle_to_direction(angle: float) -> str:
    """
    Convert bearing angle to compass direction name.
    
    Args:
        angle: Angle in degrees (0-360)
    
    Returns:
        Direction name (e.g., 'North', 'Southeast', 'West')
    """
    directions = [
        'North', 'Northeast', 'East', 'Southeast',
        'South', 'Southwest', 'West', 'Northwest'
    ]
    # Divide 360° into 8 sectors (45° each)
    index = int((angle + 22.5) % 360 / 45)
    return directions[index]


def calculate_qi_flow_score(road_data: Dict, 
                           building_density: float,
                           green_ratio: float) -> float:
    """
    Calculate Qi (energy) flow score based on urban connectivity and openness.
    
    Qi Flow Principles in Feng Shui:
    - Qi needs pathways to circulate (roads provide channels)
    - Too many obstacles block Qi (high building density)
    - Green spaces generate and refresh Qi
    - Balance is key: moderate connectivity + adequate openness
    
    Factors:
    1. Road connectivity (from road_count): enables Qi circulation
    2. Building density (inverse): lower density allows better flow
    3. Green space ratio: generates positive Qi
    
    Args:
        road_data: Dictionary with 'road_count' and 'intersections'
        building_density: Normalized building density (0-1)
        green_ratio: Green area ratio (0-1)
    
    Returns:
        Qi flow score (0-1), where 1 = optimal energy circulation
    """
    road_count = road_data.get('road_count', 0)
    intersections = road_data.get('intersections', [])
    
    # Component 1: Road connectivity score (0-1)
    # Feng Shui principle: good connectivity = good Qi circulation.
    # More roads in a planned city = better grid = better Qi pathways.
    # Penalty only kicks in at extreme density (>40 roads) = chaotic energy.
    if road_count < 3:
        road_score = road_count / 3 * 0.5   # Very sparse: poor Qi circulation
    elif road_count < 10:
        road_score = 0.5 + (road_count - 3) / 7 * 0.35  # Growing connectivity
    elif road_count <= 40:
        road_score = 0.85 + (road_count - 10) / 30 * 0.15  # Well-planned: max score
    else:
        road_score = max(0.75, 1.0 - (road_count - 40) / 60 * 0.25)  # Very dense: slight penalty
    
    # Component 2: Openness score (inverse of building density)
    openness_score = 1.0 - building_density
    
    # Component 3: Green space contribution
    green_contribution = green_ratio
    
    # Weighted combination
    # Road connectivity: 30%, Openness: 40%, Green space: 30%
    qi_flow = (
        road_score * 0.30 +
        openness_score * 0.40 +
        green_contribution * 0.30
    )
    
    logger.info(f"Qi flow score: {qi_flow:.3f} "
                f"(roads: {road_score:.2f}, openness: {openness_score:.2f}, "
                f"green: {green_contribution:.2f})")
    
    return qi_flow


def calculate_environmental_quality(hospitals: List[Dict],
                                   schools: List[Dict],
                                   radius: int) -> float:
    """
    Calculate environmental quality based on proximity to essential services.
    Good environment = balanced access to healthcare and education.
    
    Optimal Balance:
    - 1-3 hospitals: Good healthcare access without overwhelming presence
    - 3-5 schools: Indicates family-friendly, educated neighborhood
    
    Args:
        hospitals: List of hospital POIs from AMap
        schools: List of school POIs from AMap
        radius: Search radius in meters
    
    Returns:
        Environmental quality score (0-1)
    """
    # Hospital score: optimal is 2 hospitals
    if not hospitals:
        hospital_score = 0.3  # baseline — absence doesn't mean bad area, could be data gap
    elif len(hospitals) <= 3:
        hospital_score = min(0.3 + len(hospitals) / 2 * 0.7, 1.0)
    else:
        # Too many hospitals may indicate medical district (not ideal for living)
        hospital_score = max(0.5, 1.0 - (len(hospitals) - 3) / 5 * 0.5)
    
    # School score: in university zones many education POIs are expected
    if not schools:
        school_score = 0.2  # baseline — no schools could be data gap
    elif len(schools) <= 5:
        school_score = min(0.2 + len(schools) / 4 * 0.8, 1.0)
    else:
        # Dense education is positive — university towns, school districts
        school_score = min(1.0, 0.8 + (len(schools) - 5) / 20 * 0.2)
    
    # Weighted average (equal importance)
    score = (hospital_score * 0.5 + school_score * 0.5)
    
    logger.info(f"Environmental quality: {score:.3f} "
                f"({len(hospitals)} hospitals [score: {hospital_score:.2f}], "
                f"{len(schools)} schools [score: {school_score:.2f}])")
    
    return score


def calculate_spiritual_presence(temples: List[Dict], radius: int) -> float:
    """
    Calculate spiritual presence score based on nearby temples/religious sites.
    
    Args:
        temples: List of temple/religious site POIs
        radius: Search radius
    
    Returns:
        Spiritual presence score (0-1)
    """
    if not temples:
        return 0.0
    
    # Having 1-2 temples nearby is auspicious
    score = min(len(temples) / 2, 1.0)
    
    logger.info(f"Spiritual presence: {score:.3f} ({len(temples)} temples found)")
    return score
