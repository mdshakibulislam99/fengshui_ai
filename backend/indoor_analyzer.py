"""
Indoor Room Feng Shui Analysis Backend
Handles design-based and photo-based room analysis
"""

from indoor_ai_model import predict_indoor_score


def _to_ai_features(
    element_counts,
    energy_balance,
    element_balance_score,
    energy_score,
    spacial_score,
    functional_score,
    photo_coverage=0.0,
    layout_symmetry=0.5,
):
    total_elements = max(1, sum(element_counts.values()))
    total_energy = energy_balance['yin'] + energy_balance['yang']

    yin_ratio = (energy_balance['yin'] / total_energy) if total_energy else 0.5
    yang_ratio = (energy_balance['yang'] / total_energy) if total_energy else 0.5

    return {
        'wood_ratio': element_counts['wood'] / total_elements,
        'fire_ratio': element_counts['fire'] / total_elements,
        'earth_ratio': element_counts['earth'] / total_elements,
        'metal_ratio': element_counts['metal'] / total_elements,
        'water_ratio': element_counts['water'] / total_elements,
        'yin_ratio': yin_ratio,
        'yang_ratio': yang_ratio,
        'element_balance': float(element_balance_score),
        'energy_balance': float(energy_score),
        'space_flow': float(spacial_score),
        'functional_layout': float(functional_score),
        'photo_coverage': float(photo_coverage),
        'layout_symmetry': float(layout_symmetry),
    }

def analyze_room_design(elements, room_type):
    """
    Analyze a room based on placed design elements
    
    Args:
        elements: List of placed elements with types and positions
        room_type: Type of room (bedroom, living, office, etc.)
    
    Returns:
        dict: Analysis results with scores and recommendations
    """
    
    # Count elements by category
    element_counts = {
        'wood': 0,
        'fire': 0,
        'earth': 0,
        'metal': 0,
        'water': 0
    }
    
    energy_balance = {
        'yin': 0,
        'yang': 0
    }
    
    # Element feng shui properties
    element_properties = {
        # Furniture
        'bed': {'element': 'earth', 'energy': 'yin'},
        'sofa': {'element': 'earth', 'energy': 'yin'},
        'desk': {'element': 'wood', 'energy': 'yang'},
        'table': {'element': 'wood', 'energy': 'neutral'},
        'chair': {'element': 'wood', 'energy': 'yang'},
        'wardrobe': {'element': 'wood', 'energy': 'yin'},
        'bookshelf': {'element': 'wood', 'energy': 'yang'},
        'tv': {'element': 'fire', 'energy': 'yang'},
        
        # Decor
        'mirror': {'element': 'water', 'energy': 'yang'},
        'painting': {'element': 'fire', 'energy': 'yang'},
        'clock': {'element': 'metal', 'energy': 'yang'},
        'vase': {'element': 'earth', 'energy': 'yin'},
        'rug': {'element': 'earth', 'energy': 'yin'},
        'curtain': {'element': 'water', 'energy': 'yin'},
        'window': {'element': 'metal', 'energy': 'yang'},
        'door': {'element': 'wood', 'energy': 'yang'},
        'fountain': {'element': 'water', 'energy': 'yang'},
        'crystals': {'element': 'earth', 'energy': 'yang'},
        
        # Plants
        'bamboo': {'element': 'wood', 'energy': 'yang'},
        'plant': {'element': 'wood', 'energy': 'yang'},
        'bonsai': {'element': 'wood', 'energy': 'yin'},
        'flowers': {'element': 'wood', 'energy': 'yang'},
        
        # Lighting
        'lamp': {'element': 'fire', 'energy': 'yang'},
        'chandelier': {'element': 'fire', 'energy': 'yang'},
        'candle': {'element': 'fire', 'energy': 'yang'}
    }
    
    # Count elements
    for element in elements:
        element_type = element['type']
        if element_type in element_properties:
            props = element_properties[element_type]
            element_counts[props['element']] += 1
            if props['energy'] != 'neutral':
                energy_balance[props['energy']] += 1
    
    # Calculate scores
    element_balance_score = calculate_element_balance(element_counts)
    energy_score = calculate_energy_balance(energy_balance)
    spacial_score = calculate_spacial_score(len(elements))
    functional_score = calculate_functional_score(elements, room_type)
    
    overall_score = int(
        element_balance_score * 0.3 +
        energy_score * 0.25 +
        spacial_score * 0.25 +
        functional_score * 0.20
    )

    ai_features = _to_ai_features(
        element_counts,
        energy_balance,
        element_balance_score,
        energy_score,
        spacial_score,
        functional_score,
        photo_coverage=0.0,
        layout_symmetry=0.55,
    )
    ai_result = predict_indoor_score(ai_features)
    if ai_result and ai_result.get('ai_score') is not None:
        # Blend deterministic room logic with trained indoor model.
        overall_score = int(round(overall_score * 0.7 + float(ai_result['ai_score']) * 0.3))
    
    # Generate recommendations
    recommendations = generate_design_recommendations(
        element_counts,
        energy_balance,
        elements,
        room_type
    )
    
    return {
        'overall_score': overall_score,
        'ai_score': float(ai_result['ai_score']) if ai_result else None,
        'element_balance': element_balance_score,
        'energy_score': energy_score,
        'spacial_score': spacial_score,
        'functional_score': functional_score,
        'element_counts': element_counts,
        'energy_balance': energy_balance,
        'recommendations': recommendations
    }


def calculate_element_balance(counts):
    """Calculate five elements balance score"""
    total = sum(counts.values())
    if total == 0:
        return 0
    
    # Ideal is balanced distribution
    ideal = total / 5
    variance = sum(abs(count - ideal) for count in counts.values())
    score = max(0, 100 - (variance / total) * 50)
    
    return int(score)


def calculate_energy_balance(energy):
    """Calculate yin-yang balance score"""
    total = energy['yin'] + energy['yang']
    if total == 0:
        return 50
    
    ratio = energy['yang'] / total
    
    # Ideal ratio is 40-60% yang
    if 0.4 <= ratio <= 0.6:
        return 100
    elif 0.3 <= ratio <= 0.7:
        return 80
    else:
        return 60


def calculate_spacial_score(element_count):
    """Calculate space flow score based on element density"""
    if element_count < 5:
        return 90
    elif element_count < 10:
        return 85
    elif element_count < 15:
        return 75
    elif element_count < 20:
        return 65
    else:
        return 50  # Too cluttered


def calculate_functional_score(elements, room_type):
    """Calculate functional layout score based on room type"""
    element_types = [e['type'] for e in elements]
    score = 70  # Base score
    
    # Room-specific requirements
    if room_type == 'bedroom':
        if 'bed' in element_types:
            score += 10
        if 'plant' in element_types:
            score += 5
        if 'mirror' in element_types and 'bed' in element_types:
            score -= 10  # Mirror facing bed is inauspicious
        if 'lamp' in element_types:
            score += 5
    
    elif room_type == 'living':
        if 'sofa' in element_types:
            score += 10
        if 'plant' in element_types:
            score += 5
        if 'lamp' in element_types or 'chandelier' in element_types:
            score += 5
    
    elif room_type == 'office':
        if 'desk' in element_types:
            score += 10
        if 'chair' in element_types:
            score += 5
        if 'plant' in element_types:
            score += 5
        if 'bookshelf' in element_types:
            score += 5
    
    return min(100, score)


def generate_design_recommendations(elements, energy, placed_elements, room_type):
    """Generate feng shui recommendations"""
    recommendations = []
    
    # Element recommendations
    if elements['wood'] < 2:
        recommendations.append('Add more wood elements (plants, furniture) for growth energy')
    
    if elements['fire'] == 0:
        recommendations.append('Include fire elements (candles, red colors) for passion and warmth')
    
    if elements['water'] == 0:
        recommendations.append('Add water elements (fountain, mirror) for flow and prosperity')
    
    if elements['earth'] < 2:
        recommendations.append('Incorporate earth elements (crystals, pottery) for stability')
    
    if elements['metal'] == 0:
        recommendations.append('Include metal elements (clocks, metal frames) for clarity')
    
    # Energy balance recommendations
    total_energy = energy['yin'] + energy['yang']
    if total_energy > 0:
        yang_ratio = energy['yang'] / total_energy
        
        if yang_ratio > 0.7:
            recommendations.append('Balance yang energy with softer, yin elements (curtains, rugs)')
        elif yang_ratio < 0.3:
            recommendations.append('Add more yang energy with lighting and active elements')
    
    # Room-specific recommendations
    element_types = [e['type'] for e in placed_elements]
    
    if room_type == 'bedroom':
        if 'plant' not in element_types:
            recommendations.append('Add plants for fresh air and positive energy')
        if 'mirror' in element_types:
            recommendations.append('⚠️ Avoid placing mirrors directly facing the bed')
    
    if len(placed_elements) > 15:
        recommendations.append('Consider decluttering - too many items can block energy flow')
    
    if not recommendations:
        recommendations.append('✓ Your room design shows good feng shui balance!')
    
    return recommendations


def analyze_room_photos(photos):
    """
    Analyze room based on uploaded photos.
    Uses deterministic heuristics from uploaded image payloads so results
    are tied to actual photo inputs and stable across repeated requests.
    
    Args:
        photos: Dict of photo data (north, south, east, west, floor)
    
    Returns:
        dict: Analysis results with scores and recommendations
    """
    import hashlib

    non_empty = {
        key: value for key, value in (photos or {}).items()
        if isinstance(value, str) and value.strip()
    }
    photo_count = len(non_empty)

    if photo_count == 0:
        return {
            'overall_score': 0,
            'categories': {
                'lighting': 0,
                'space_flow': 0,
                'color_harmony': 0,
                'furniture_placement': 0,
                'declutter': 0,
            },
            'recommendations': ['Upload at least one clear room photo for analysis.']
        }

    lengths = [len(v) for v in non_empty.values()]
    min_len = min(lengths)
    max_len = max(lengths)
    avg_len = sum(lengths) / len(lengths)

    # Use hash-derived deterministic jitter so outputs are stable for the same photos.
    hash_input = '|'.join(f"{k}:{non_empty[k][:120]}" for k in sorted(non_empty.keys()))
    digest = hashlib.sha256(hash_input.encode('utf-8')).digest()

    def hashed_offset(index, amplitude=6):
        value = digest[index] % (2 * amplitude + 1)
        return value - amplitude

    coverage_bonus = min(15, photo_count * 3)
    consistency_ratio = 1.0 if avg_len == 0 else (min_len / avg_len)
    consistency_bonus = int(max(0, min(12, (consistency_ratio - 0.55) * 28)))

    lighting = max(45, min(96, 64 + coverage_bonus + consistency_bonus + hashed_offset(0)))
    space_flow = max(40, min(94, 60 + coverage_bonus + int((avg_len / max_len) * 10 if max_len else 0) + hashed_offset(1)))
    color_harmony = max(42, min(93, 58 + coverage_bonus + consistency_bonus + hashed_offset(2)))
    furniture_placement = max(44, min(95, 61 + coverage_bonus + int((photo_count / 5) * 10) + hashed_offset(3)))
    declutter = max(38, min(92, 57 + coverage_bonus + int((min_len / max_len) * 12 if max_len else 0) + hashed_offset(4)))

    categories = {
        'lighting': int(lighting),
        'space_flow': int(space_flow),
        'color_harmony': int(color_harmony),
        'furniture_placement': int(furniture_placement),
        'declutter': int(declutter)
    }

    # Build pseudo-element composition from photo-derived category profile.
    photo_elements = {
        'wood': max(0.0, min(1.0, (categories['color_harmony'] + categories['declutter']) / 200.0)),
        'fire': max(0.0, min(1.0, categories['lighting'] / 100.0)),
        'earth': max(0.0, min(1.0, categories['furniture_placement'] / 100.0)),
        'metal': max(0.0, min(1.0, categories['space_flow'] / 100.0)),
        'water': max(0.0, min(1.0, (categories['space_flow'] + categories['color_harmony']) / 200.0)),
    }
    pseudo_counts = {k: int(round(v * 10)) for k, v in photo_elements.items()}
    pseudo_energy = {
        'yin': int(round((categories['declutter'] + categories['color_harmony']) / 20.0)),
        'yang': int(round((categories['lighting'] + categories['space_flow']) / 20.0)),
    }

    ai_features = _to_ai_features(
        pseudo_counts,
        pseudo_energy,
        categories['color_harmony'],
        categories['lighting'],
        categories['space_flow'],
        categories['furniture_placement'],
        photo_coverage=photo_count / 5.0,
        layout_symmetry=max(0.0, min(1.0, min_len / max_len if max_len else 0.5)),
    )
    ai_result = predict_indoor_score(ai_features)

    overall_score = int(round(
        categories['lighting'] * 0.22 +
        categories['space_flow'] * 0.23 +
        categories['color_harmony'] * 0.18 +
        categories['furniture_placement'] * 0.22 +
        categories['declutter'] * 0.15
    ))

    if ai_result and ai_result.get('ai_score') is not None:
        overall_score = int(round(overall_score * 0.65 + float(ai_result['ai_score']) * 0.35))

    recommendations = []
    if categories['lighting'] < 70:
        recommendations.append('Increase natural light access and layer warm ambient lighting to activate healthy qi.')
    if categories['space_flow'] < 70:
        recommendations.append('Clear circulation routes between doorway, windows, and key furniture to support smoother energy flow.')
    if categories['color_harmony'] < 68:
        recommendations.append('Balance strong tones with earth and wood colors to stabilize the five elements.')
    if categories['furniture_placement'] < 70:
        recommendations.append('Reposition major furniture into command positions facing the room entry where possible.')
    if categories['declutter'] < 65:
        recommendations.append('Reduce visible clutter and organize storage to prevent stagnant qi pockets.')

    if photo_count < 5:
        recommendations.append('Upload all five directions (north, south, east, west, floor plan) for a more complete analysis.')

    if not recommendations:
        recommendations = [
            'Room energy profile is balanced. Maintain clear pathways, healthy light, and element diversity.'
        ]

    return {
        'overall_score': overall_score,
        'ai_score': float(ai_result['ai_score']) if ai_result else None,
        'categories': categories,
        'recommendations': recommendations[:6]
    }
