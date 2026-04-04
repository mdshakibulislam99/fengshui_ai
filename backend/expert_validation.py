# Expert validation and feedback tracking module
# Enables learning from Feng Shui expert assessments to improve model accuracy

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib

logger = logging.getLogger(__name__)

# Expert validation storage
EXPERT_VALIDATION_FILE = os.path.join(os.path.dirname(__file__), 'data', 'expert_validations.json')

def _ensure_data_dir():
    """Ensure data directory exists."""
    data_dir = os.path.dirname(EXPERT_VALIDATION_FILE)
    os.makedirs(data_dir, exist_ok=True)


def _load_expert_validations() -> Dict[str, Any]:
    """Load expert validation records from file."""
    _ensure_data_dir()
    if os.path.exists(EXPERT_VALIDATION_FILE):
        try:
            with open(EXPERT_VALIDATION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load expert validations: {e}")
    
    return {
        'validations': [],
        'expert_profiles': {},
        'learning_summary': {
            'total_assessments': 0,
            'avg_divergence': 0.0,
            'significant_divergences': 0,
            'high_confidence_experts': []
        }
    }


def _save_expert_validations(data: Dict[str, Any]) -> bool:
    """Save expert validation records to file."""
    _ensure_data_dir()
    try:
        with open(EXPERT_VALIDATION_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save expert validations: {e}")
        return False


def record_expert_assessment(
    expert_id: str,
    expert_name: str,
    location_lat: float,
    location_lng: float,
    location_address: str,
    expert_score: float,
    ai_score: float,
    category_assessments: Optional[Dict[str, float]] = None,
    feedback: str = "",
    confidence_level: str = "moderate"  # high, moderate, low
) -> Dict[str, Any]:
    """
    Record an expert Feng Shui assessment for model validation and learning.
    
    Args:
        expert_id: Unique identifier for expert
        expert_name: Expert's name
        location_lat: Location latitude
        location_lng: Location longitude
        location_address: Location address/description
        expert_score: Expert's assessment (0-100)
        ai_score: System's AI score (0-100)
        category_assessments: Dict of category scores from expert
        feedback: Expert commentary
        confidence_level: Expert's confidence in their assessment
    
    Returns:
        Assessment record
    """
    # Create location hash for tracking
    location_key = f"{location_lat:.4f},{location_lng:.4f}"
    location_hash = hashlib.md5(location_key.encode()).hexdigest()[:12]
    
    # Calculate divergence
    divergence = abs(expert_score - ai_score)
    is_significant = divergence > 15
    
    assessment: Dict[str, Any] = {
        'timestamp': datetime.now().isoformat(),
        'expert_id': expert_id,
        'expert_name': expert_name,
        'location_hash': location_hash,
        'location': {
            'latitude': location_lat,
            'longitude': location_lng,
            'address': location_address
        },
        'scores': {
            'expert_score': float(expert_score),
            'ai_score': float(ai_score),
            'divergence': float(divergence),
            'is_significant_divergence': is_significant
        },
        'category_assessments': category_assessments or {},
        'feedback': feedback,
        'confidence_level': confidence_level
    }
    
    # Load and update validation records
    validations = _load_expert_validations()
    validations['validations'].append(assessment)
    
    # Update expert profile
    if expert_id not in validations['expert_profiles']:
        validations['expert_profiles'][expert_id] = {
            'name': expert_name,
            'assessment_count': 0,
            'avg_divergence': 0.0,
            'expertise_level': 'developing'
        }
    
    expert_profile = validations['expert_profiles'][expert_id]
    expert_profile['assessment_count'] += 1
    
    # Update running average divergence
    prev_avg = expert_profile['avg_divergence']
    count = expert_profile['assessment_count']
    expert_profile['avg_divergence'] = (prev_avg * (count - 1) + divergence) / count
    
    # Determine expertise level (lower avg divergence = higher expertise)
    if expert_profile['avg_divergence'] < 5:
        expert_profile['expertise_level'] = 'master'
    elif expert_profile['avg_divergence'] < 10:
        expert_profile['expertise_level'] = 'advanced'
    elif expert_profile['avg_divergence'] < 15:
        expert_profile['expertise_level'] = 'proficient'
    else:
        expert_profile['expertise_level'] = 'developing'
    
    # Update learning summary
    summary = validations['learning_summary']
    summary['total_assessments'] += 1
    prev_total_div = summary['avg_divergence'] * max(1, summary['total_assessments'] - 1)
    summary['avg_divergence'] = (prev_total_div + divergence) / summary['total_assessments']
    
    if is_significant:
        summary['significant_divergences'] += 1
    
    # Identify high confidence experts
    if expert_profile['expertise_level'] == 'master' and expert_id not in summary['high_confidence_experts']:
        summary['high_confidence_experts'].append(expert_id)
    
    # Save updated validations
    _save_expert_validations(validations)
    
    logger.info(
        f"Expert assessment recorded: {expert_name} "
        f"(Expert={expert_score:.0f}, AI={ai_score:.0f}, Diff={divergence:.1f})"
    )
    
    return assessment


def get_expert_profile(expert_id: str) -> Optional[Dict[str, Any]]:
    """Get an expert's profile and assessment history."""
    validations = _load_expert_validations()
    
    if expert_id not in validations['expert_profiles']:
        return None
    
    profile = validations['expert_profiles'][expert_id]
    assessments = [v for v in validations['validations'] if v['expert_id'] == expert_id]
    
    return {
        'profile': profile,
        'assessment_count': len(assessments),
        'assessments': assessments[-10:]  # Last 10 assessments
    }


def get_learning_summary() -> Dict[str, Any]:
    """Get overall learning summary from expert validations."""
    validations = _load_expert_validations()
    summary = validations['learning_summary']
    expert_profiles = validations['expert_profiles']
    
    return {
        'total_assessments': summary['total_assessments'],
        'average_divergence': round(summary['avg_divergence'], 2),
        'significant_divergences_count': summary['significant_divergences'],
        'significant_divergence_percentage': (
            round(summary['significant_divergences'] / max(1, summary['total_assessments']) * 100, 1)
            if summary['total_assessments'] > 0 else 0
        ),
        'expert_count': len(expert_profiles),
        'high_confidence_experts': summary['high_confidence_experts'],
        'expertise_distribution': {
            'master': len([e for e in expert_profiles.values() if e['expertise_level'] == 'master']),
            'advanced': len([e for e in expert_profiles.values() if e['expertise_level'] == 'advanced']),
            'proficient': len([e for e in expert_profiles.values() if e['expertise_level'] == 'proficient']),
            'developing': len([e for e in expert_profiles.values() if e['expertise_level'] == 'developing']),
        },
        'recommendation': _generate_learning_recommendation(validations)
    }


def _generate_learning_recommendation(validations: Dict[str, Any]) -> str:
    """Generate recommendation based on validation results."""
    summary = validations['learning_summary']
    
    if summary['total_assessments'] < 10:
        return "Need more expert assessments (min 10) to generate meaningful recommendations"
    
    avg_div = summary['avg_divergence']
    
    if avg_div < 5:
        return "Excellent agreement with experts. Model is well-calibrated."
    elif avg_div < 10:
        return "Good agreement with experts. Consider refining water and orientation detection."
    elif avg_div < 15:
        return "Moderate agreement. Recommend training with more expert data and seasonal adjustments."
    else:
        return "Significant divergence. Recommend comprehensive retraining with expert feedback."


def get_significant_divergences(limit: int = 10) -> List[Dict[str, Any]]:
    """Get cases where model diverges significantly from experts."""
    validations = _load_expert_validations()
    
    divergences = [
        v for v in validations['validations'] 
        if v['scores']['is_significant_divergence']
    ]
    
    # Sort by divergence amount (highest first)
    divergences.sort(key=lambda x: x['scores']['divergence'], reverse=True)
    
    return divergences[:limit]
