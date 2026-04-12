# AI model module for training, loading, and predicting Feng Shui scores

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import logging
import os
from typing import Dict, List, Tuple, Optional

from real_location_training_data import (
    ARCHETYPE_FEATURE_CENTERS,
    REAL_LOCATION_FENG_SHUI_SEEDS,
)

logger = logging.getLogger(__name__)

# Model file path
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'feng_shui_rf_model.pkl')

FEATURE_COLUMNS = [
    'green_area_ratio',
    'water_proximity',
    'building_density',
    'road_intersection_density',
    'orientation_score',
    'environmental_quality',
    'spiritual_presence',
]


def _clip_01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def generate_real_location_seed_data(n_samples: int) -> pd.DataFrame:
    """Generate feature rows sampled around 100 real location archetypes."""
    if n_samples <= 0 or not REAL_LOCATION_FENG_SHUI_SEEDS:
        return pd.DataFrame(columns=FEATURE_COLUMNS)

    rng = np.random.default_rng(42)
    seed_count = len(REAL_LOCATION_FENG_SHUI_SEEDS)
    sampled_indices = rng.integers(0, seed_count, size=n_samples)
    rows = []

    for idx in sampled_indices:
        seed = REAL_LOCATION_FENG_SHUI_SEEDS[int(idx)]
        archetype = str(seed.get('archetype', 'balanced_urban'))
        center = ARCHETYPE_FEATURE_CENTERS.get(
            archetype,
            ARCHETYPE_FEATURE_CENTERS['balanced_urban']
        )

        latitude = float(seed.get('latitude', 0.0))
        climate_green_adjust = 0.0
        if abs(latitude) > 45:
            climate_green_adjust = -0.04
        elif abs(latitude) < 12:
            climate_green_adjust = 0.03

        rows.append({
            'green_area_ratio': _clip_01(rng.normal(center['green_area_ratio'] + climate_green_adjust, 0.08)),
            'water_proximity': _clip_01(rng.normal(center['water_proximity'], 0.08)),
            'building_density': _clip_01(rng.normal(center['building_density'], 0.08)),
            'road_intersection_density': _clip_01(rng.normal(center['road_intersection_density'], 0.08)),
            'orientation_score': _clip_01(rng.normal(center['orientation_score'], 0.07)),
            'environmental_quality': _clip_01(rng.normal(center['environmental_quality'], 0.07)),
            'spiritual_presence': _clip_01(rng.normal(center['spiritual_presence'], 0.08)),
        })

    return pd.DataFrame(rows, columns=FEATURE_COLUMNS)


def generate_synthetic_data(n_samples: int = 1000) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Generate synthetic urban environmental data for training.
    
    Features:
    - green_area_ratio: 0-1 (higher is better)
    - water_proximity: 0-1 (higher is better)
    - building_density: 0-1 (lower is better)
    - road_intersection_density: 0-1 (moderate is best)
    - orientation_score: 0-1 (higher is better)
    - environmental_quality: 0-1 (higher is better)
    - spiritual_presence: 0-1 (higher is better)
    
    Labels: Feng Shui score 0-100 (rule-based logic)
    
    Args:
        n_samples: Number of samples to generate
    
    Returns:
        Tuple of (features DataFrame, labels array)
    """
    logger.info(f"Generating {n_samples} training samples (synthetic + real-location seeds)...")

    np.random.seed(42)

    # Keep a meaningful real-location share, with a floor of 100 for medium+ runs.
    real_seed_samples = int(n_samples * 0.35)
    if n_samples >= 300:
        real_seed_samples = max(100, real_seed_samples)
    real_seed_samples = min(real_seed_samples, n_samples)
    random_samples = n_samples - real_seed_samples

    random_df = pd.DataFrame(columns=FEATURE_COLUMNS)
    if random_samples > 0:
        random_data = {
            'green_area_ratio': np.random.beta(2, 5, random_samples),
            'water_proximity': np.random.beta(2, 3, random_samples),
            'building_density': np.random.beta(5, 2, random_samples),
            'road_intersection_density': np.random.beta(3, 3, random_samples),
            'orientation_score': np.random.beta(3, 2, random_samples),
            'environmental_quality': np.random.beta(3, 3, random_samples),
            'spiritual_presence': np.random.beta(2, 5, random_samples),
        }
        random_df = pd.DataFrame(random_data, columns=FEATURE_COLUMNS)

    seeded_df = generate_real_location_seed_data(real_seed_samples)
    features_df = pd.concat([random_df, seeded_df], ignore_index=True)
    features_df = features_df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    
    # Generate labels using rule-based logic
    labels = generate_rule_based_scores(features_df)
    
    logger.info(
        "Training data generated. "
        f"Seeded rows: {real_seed_samples}, random rows: {random_samples}. "
        f"Score range: {labels.min():.1f} - {labels.max():.1f}"
    )
    
    return features_df, labels


def generate_rule_based_scores(features_df: pd.DataFrame) -> np.ndarray:
    """
    Generate Feng Shui scores using IMPROVED CONTEXT-AWARE rule-based logic.
    
    Key insight: System should recognize that HIGH environmental quality indicators
    (green, orientation, environment) = HIGH feng shui score, regardless of water.
    
    Different location types (campus, waterfront, urban, mountain) have
    different optimal feature patterns. This function recognizes location
    type from features and applies appropriate scoring AND ensures good    
    locations score appropriately high.
    
    Args:
        features_df: DataFrame with feature columns
    
    Returns:
        Array of scores (0-100)
    """
    scores = []
    
    for _, row in features_df.iterrows():
        # Detect location type from feature pattern
        green = row['green_area_ratio']
        water = row['water_proximity']
        building = row['building_density']
        roads = row['road_intersection_density']
        orient = row['orientation_score']
        env_qual = row['environmental_quality']
        spirit = row['spiritual_presence']
        
        # Location type detection
        is_waterfront = water > 0.60  # High water → waterfront
        is_campus = green > 0.50 and water < 0.25 and building < 0.70  # Campus pattern
        is_dense_urban = building > 0.70 and green < 0.40  # Dense urban
        is_mountain = green > 0.60 and building < 0.40  # Mountain/rural
        
        # QUALITY SCORE: How good is this location's overall environment?
        # High green + high orientation + high environment = high quality
        quality_indicator = (green * 0.35) + (orient * 0.35) + (env_qual * 0.30)
        
        # Initialize score with quality baseline
        # Good quality locations should START at 70+
        if quality_indicator > 0.80:
            score = 75 + (quality_indicator - 0.70) * 20  # 75-100 for excellent quality
        elif quality_indicator > 0.70:
            score = 70 + (quality_indicator - 0.65) * 10  # 70-75 for good quality  
        elif quality_indicator > 0.60:
            score = 60 + (quality_indicator - 0.55) * 10  # 60-70 for moderate
        else:
            score = 50 + quality_indicator * 20  # 50-60 for poor
        
        # LOCATION TYPE ADJUSTMENTS: Add bonuses for location-specific good features
        if is_waterfront:
            # Waterfront bonus for high water  
            score += water * 10
            # Penalty for low green in waterfront
            if green < 0.30:
                score -= 10
            
        elif is_campus:
            # Campus bonus for excellent orientation
            score += (orient - 0.60) * 15 if orient > 0.60 else 0
            # Campus bonus for high env quality
            score += (env_qual - 0.60) * 10 if env_qual > 0.60 else 0
            # NO penalty for low water (it's normal)
            
        elif is_dense_urban:
            # Urban bonus for roads accessibility  
            if 0.4 < roads < 0.7:
                score += 8
            # Urban bonus for good environment despite density
            score += (env_qual - 0.60) * 8 if env_qual > 0.60 else 0
            
        elif is_mountain:
            # Mountain bonus for high green and water
            score += (green - 0.50) * 10 if green > 0.50 else 0
            score += (water - 0.40) * 8 if water > 0.40 else 0
        
        # GENERAL BONUS: Recognize excellent specific features
        if orient > 0.85:
            score += 5  # Excellent orientation helps all locations
        if env_qual > 0.75:
            score += 5  # Excellent environment helps all locations
        
        # Add slight noise for realism (±1.5 points)
        noise = np.random.normal(0, 1.5)
        score += noise
        
        # Ensure score is in valid range
        score = np.clip(score, 0, 100)
        
        scores.append(score)
    
    return np.array(scores)


def train_model(n_samples: int = 1000, test_size: float = 0.2) -> Dict:
    """
    Train a Random Forest Regressor on synthetic data.
    
    Args:
        n_samples: Number of synthetic samples to generate
        test_size: Proportion of data for testing
    
    Returns:
        Dictionary with training metrics and model info
    """
    logger.info("Starting Random Forest model training...")
    
    # Generate synthetic data
    X, y = generate_synthetic_data(n_samples)
    
    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )
    
    logger.info(f"Training set size: {len(X_train)}, Test set size: {len(X_test)}")
    
    # Initialize Random Forest model
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    # Train the model
    logger.info("Training model...")
    model.fit(X_train, y_train)
    
    # Evaluate on test set
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    logger.info(f"Model training complete. MSE: {mse:.2f}, R²: {r2:.3f}")
    
    # Save the model
    save_model(model, X.columns.tolist())
    
    return {
        'mse': mse,
        'r2': r2,
        'feature_names': X.columns.tolist(),
        'n_samples': n_samples,
        'model_path': MODEL_PATH
    }


def save_model(model: RandomForestRegressor, feature_names: List[str]):
    """
    Save the trained model to disk.
    
    Args:
        model: Trained RandomForestRegressor
        feature_names: List of feature names
    """
    # Create models directory if it doesn't exist
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    # Save model and metadata
    model_data = {
        'model': model,
        'feature_names': feature_names
    }
    
    joblib.dump(model_data, MODEL_PATH)
    logger.info(f"Model saved to {MODEL_PATH}")


def load_model() -> Optional[Tuple[RandomForestRegressor, List[str]]]:
    """
    Load the trained model from disk.
    
    Returns:
        Tuple of (model, feature_names) or None if model doesn't exist
    """
    if not os.path.exists(MODEL_PATH):
        logger.warning(f"Model file not found at {MODEL_PATH}")
        return None
    
    try:
        model_data = joblib.load(MODEL_PATH)
        logger.info("Model loaded successfully")
        return model_data['model'], model_data['feature_names']
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return None


def predict_feng_shui_score(features: Dict) -> Optional[Dict]:
    """
    Predict Feng Shui score using the trained Random Forest model.
    
    Args:
        features: Dictionary of extracted features
    
    Returns:
        Dictionary with prediction and feature importance,
        or None if model is not available
    """
    # Load the model
    model_data = load_model()
    
    if model_data is None:
        logger.warning("Model not found. Training a new model...")
        train_model()
        model_data = load_model()
        
        if model_data is None:
            logger.error("Failed to train and load model")
            return None
    
    model, feature_names = model_data
    
    # Prepare features in correct order
    try:
        feature_values = [features.get(name, 0.0) for name in feature_names]
        X = np.array(feature_values).reshape(1, -1)
        
        # Make prediction
        predicted_score = model.predict(X)[0]
        
        # Ensure score is in valid range
        predicted_score = np.clip(predicted_score, 0, 100)
        
        # Get feature importance
        feature_importance = get_feature_importance(model, feature_names, feature_values)
        
        logger.info(f"AI predicted score: {predicted_score:.2f}")
        
        return {
            'ai_score': predicted_score,
            'feature_importance': feature_importance
        }
        
    except Exception as e:
        logger.error(f"Error making prediction: {str(e)}")
        return None


def get_feature_importance(model: RandomForestRegressor,
                          feature_names: List[str],
                          feature_values: List[float]) -> Dict:
    """
    Extract feature importance from Random Forest model.
    
    Args:
        model: Trained RandomForestRegressor
        feature_names: List of feature names
        feature_values: List of feature values for current prediction
    
    Returns:
        Dictionary with feature importance and explanations
    """
    # Get feature importance from model
    importances = model.feature_importances_
    
    # Combine with feature names and values
    importance_data = []
    for name, importance, value in zip(feature_names, importances, feature_values):
        importance_data.append({
            'feature': name,
            'importance': float(importance),
            'value': float(value),
            'contribution': float(importance * value * 100)  # Approximate contribution to score
        })
    
    # Sort by importance
    importance_data.sort(key=lambda x: x['importance'], reverse=True)
    
    return {
        'feature_importance': importance_data,
        'explanations': generate_ai_explanations(importance_data)
    }


def generate_ai_explanations(importance_data: List[Dict]) -> List[str]:
    """
    Generate human-readable explanations based on feature importance.
    
    Args:
        importance_data: List of feature importance dictionaries
    
    Returns:
        List of explanation strings
    """
    explanations = []
    
    # Get top 3 most important features
    top_features = importance_data[:3]
    
    feature_descriptions = {
        'green_area_ratio': ('green space coverage', 'vegetation and parks'),
        'water_proximity': ('water element proximity', 'rivers and lakes'),
        'building_density': ('building density', 'urban crowding'),
        'road_intersection_density': ('road network density', 'traffic flow'),
        'orientation_score': ('building orientation', 'directional alignment'),
        'environmental_quality': ('environmental quality', 'nearby amenities'),
        'spiritual_presence': ('spiritual energy', 'sacred sites')
    }
    
    explanations.append("🤖 AI Model Analysis:")
    
    for i, item in enumerate(top_features, 1):
        feature = item['feature']
        importance = item['importance']
        value = item['value']
        
        desc, detail = feature_descriptions.get(feature, (feature, feature))
        
        if value > 0.7:
            quality = "excellent"
        elif value > 0.5:
            quality = "good"
        elif value > 0.3:
            quality = "moderate"
        else:
            quality = "low"
        
        explanations.append(
            f"  {i}. {desc.title()} is the {'most' if i == 1 else 'next'} influential factor "
            f"(importance: {importance:.1%}), with {quality} value ({value:.2f})."
        )
    
    return explanations
