"""Indoor room feng shui training seeds.

This module provides 100 deterministic room samples for indoor model training.
"""

from typing import Dict, List, Union


INDOOR_FEATURE_COLUMNS = [
    "wood_ratio",
    "fire_ratio",
    "earth_ratio",
    "metal_ratio",
    "water_ratio",
    "yin_ratio",
    "yang_ratio",
    "element_balance",
    "energy_balance",
    "space_flow",
    "functional_layout",
    "photo_coverage",
    "layout_symmetry",
]


_ROOM_ARCHETYPES: List[Dict[str, Union[str, float]]] = [
    {
        "name": "balanced_bedroom",
        "wood_ratio": 0.24,
        "fire_ratio": 0.12,
        "earth_ratio": 0.26,
        "metal_ratio": 0.18,
        "water_ratio": 0.20,
        "yin_ratio": 0.58,
        "yang_ratio": 0.42,
        "element_balance": 84,
        "energy_balance": 88,
        "space_flow": 83,
        "functional_layout": 86,
        "photo_coverage": 0.90,
        "layout_symmetry": 0.76,
        "target_score": 86,
    },
    {
        "name": "cluttered_bedroom",
        "wood_ratio": 0.14,
        "fire_ratio": 0.27,
        "earth_ratio": 0.30,
        "metal_ratio": 0.06,
        "water_ratio": 0.23,
        "yin_ratio": 0.30,
        "yang_ratio": 0.70,
        "element_balance": 57,
        "energy_balance": 52,
        "space_flow": 44,
        "functional_layout": 58,
        "photo_coverage": 0.72,
        "layout_symmetry": 0.42,
        "target_score": 54,
    },
    {
        "name": "balanced_living",
        "wood_ratio": 0.22,
        "fire_ratio": 0.16,
        "earth_ratio": 0.24,
        "metal_ratio": 0.17,
        "water_ratio": 0.21,
        "yin_ratio": 0.47,
        "yang_ratio": 0.53,
        "element_balance": 82,
        "energy_balance": 84,
        "space_flow": 86,
        "functional_layout": 85,
        "photo_coverage": 0.90,
        "layout_symmetry": 0.78,
        "target_score": 87,
    },
    {
        "name": "dark_living",
        "wood_ratio": 0.20,
        "fire_ratio": 0.06,
        "earth_ratio": 0.28,
        "metal_ratio": 0.24,
        "water_ratio": 0.22,
        "yin_ratio": 0.70,
        "yang_ratio": 0.30,
        "element_balance": 74,
        "energy_balance": 55,
        "space_flow": 64,
        "functional_layout": 69,
        "photo_coverage": 0.80,
        "layout_symmetry": 0.66,
        "target_score": 66,
    },
    {
        "name": "command_office",
        "wood_ratio": 0.28,
        "fire_ratio": 0.14,
        "earth_ratio": 0.18,
        "metal_ratio": 0.20,
        "water_ratio": 0.20,
        "yin_ratio": 0.43,
        "yang_ratio": 0.57,
        "element_balance": 82,
        "energy_balance": 86,
        "space_flow": 81,
        "functional_layout": 90,
        "photo_coverage": 0.92,
        "layout_symmetry": 0.79,
        "target_score": 88,
    },
    {
        "name": "chaotic_office",
        "wood_ratio": 0.10,
        "fire_ratio": 0.30,
        "earth_ratio": 0.20,
        "metal_ratio": 0.26,
        "water_ratio": 0.14,
        "yin_ratio": 0.24,
        "yang_ratio": 0.76,
        "element_balance": 52,
        "energy_balance": 48,
        "space_flow": 42,
        "functional_layout": 51,
        "photo_coverage": 0.70,
        "layout_symmetry": 0.36,
        "target_score": 49,
    },
    {
        "name": "minimal_studio",
        "wood_ratio": 0.23,
        "fire_ratio": 0.11,
        "earth_ratio": 0.22,
        "metal_ratio": 0.24,
        "water_ratio": 0.20,
        "yin_ratio": 0.52,
        "yang_ratio": 0.48,
        "element_balance": 80,
        "energy_balance": 82,
        "space_flow": 90,
        "functional_layout": 78,
        "photo_coverage": 0.88,
        "layout_symmetry": 0.81,
        "target_score": 84,
    },
    {
        "name": "narrow_corridor_layout",
        "wood_ratio": 0.21,
        "fire_ratio": 0.18,
        "earth_ratio": 0.31,
        "metal_ratio": 0.16,
        "water_ratio": 0.14,
        "yin_ratio": 0.45,
        "yang_ratio": 0.55,
        "element_balance": 63,
        "energy_balance": 73,
        "space_flow": 46,
        "functional_layout": 61,
        "photo_coverage": 0.84,
        "layout_symmetry": 0.40,
        "target_score": 60,
    },
    {
        "name": "well_lit_family_room",
        "wood_ratio": 0.27,
        "fire_ratio": 0.17,
        "earth_ratio": 0.22,
        "metal_ratio": 0.15,
        "water_ratio": 0.19,
        "yin_ratio": 0.44,
        "yang_ratio": 0.56,
        "element_balance": 84,
        "energy_balance": 87,
        "space_flow": 88,
        "functional_layout": 84,
        "photo_coverage": 0.94,
        "layout_symmetry": 0.77,
        "target_score": 89,
    },
    {
        "name": "over_decorated_room",
        "wood_ratio": 0.12,
        "fire_ratio": 0.24,
        "earth_ratio": 0.34,
        "metal_ratio": 0.22,
        "water_ratio": 0.08,
        "yin_ratio": 0.35,
        "yang_ratio": 0.65,
        "element_balance": 50,
        "energy_balance": 58,
        "space_flow": 39,
        "functional_layout": 56,
        "photo_coverage": 0.82,
        "layout_symmetry": 0.34,
        "target_score": 47,
    },
]


def _clip_01(value: float) -> float:
    return max(0.0, min(1.0, value))


def build_indoor_training_samples() -> List[Dict[str, float]]:
    """Create 100 deterministic indoor samples (10 archetypes x 10 variants)."""
    samples: List[Dict[str, float]] = []

    for archetype_idx, base in enumerate(_ROOM_ARCHETYPES):
        for variant in range(10):
            swing = (variant - 4.5) / 9.0
            row: Dict[str, float] = {}

            for key in INDOOR_FEATURE_COLUMNS:
                value = float(base[key])
                if key.endswith("_ratio") or key in ("photo_coverage", "layout_symmetry"):
                    row[key] = _clip_01(value + swing * 0.08)
                else:
                    row[key] = max(0.0, min(100.0, value + swing * 9.0))

            # Keep yin+yang physically coherent.
            yin = row["yin_ratio"]
            row["yang_ratio"] = _clip_01(1.0 - yin)

            score = float(base["target_score"])
            score += swing * 8.0
            score += (row["space_flow"] - 70.0) * 0.07
            score += (row["functional_layout"] - 70.0) * 0.08
            row["target_score"] = max(0.0, min(100.0, score))
            row["archetype"] = float(archetype_idx)
            samples.append(row)

    return samples


INDOOR_ROOM_TRAINING_SAMPLES = build_indoor_training_samples()
