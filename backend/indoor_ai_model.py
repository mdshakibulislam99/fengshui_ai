"""Indoor Feng Shui AI model for room design and photo-analysis scoring."""

import logging
import os
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from .indoor_room_training_data import (
    INDOOR_FEATURE_COLUMNS,
    INDOOR_ROOM_TRAINING_SAMPLES,
)


logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "models",
    "indoor_feng_shui_rf_model.pkl",
)


def _feature_vector(row: Dict) -> List[float]:
    return [float(row.get(name, 0.0)) for name in INDOOR_FEATURE_COLUMNS]


def generate_indoor_training_data(n_samples: int = 1000) -> Tuple[pd.DataFrame, np.ndarray]:
    """Build indoor training data by mixing room seeds and synthetic perturbations."""
    if n_samples < 100:
        n_samples = 100

    np.random.seed(42)
    seeds_df = pd.DataFrame(INDOOR_ROOM_TRAINING_SAMPLES)

    base_X = seeds_df[INDOOR_FEATURE_COLUMNS]
    base_y = seeds_df["target_score"].to_numpy()

    extra_count = max(0, n_samples - len(seeds_df))
    synth_rows = []
    synth_labels = []

    if extra_count > 0:
        seed_indices = np.random.randint(0, len(seeds_df), size=extra_count)
        for idx in seed_indices:
            src = seeds_df.iloc[int(idx)]
            row = {}
            for col in INDOOR_FEATURE_COLUMNS:
                value = float(src[col])
                if col.endswith("_ratio") or col in ("photo_coverage", "layout_symmetry"):
                    row[col] = float(np.clip(np.random.normal(value, 0.06), 0.0, 1.0))
                else:
                    row[col] = float(np.clip(np.random.normal(value, 6.0), 0.0, 100.0))

            row["yang_ratio"] = float(np.clip(1.0 - row["yin_ratio"], 0.0, 1.0))

            score = (
                row["element_balance"] * 0.24
                + row["energy_balance"] * 0.20
                + row["space_flow"] * 0.20
                + row["functional_layout"] * 0.20
                + row["layout_symmetry"] * 100.0 * 0.08
                + row["photo_coverage"] * 100.0 * 0.08
            )
            score += float(np.random.normal(0, 3.0))

            synth_rows.append(row)
            synth_labels.append(float(np.clip(score, 0.0, 100.0)))

    if synth_rows:
        synth_X = pd.DataFrame(synth_rows, columns=INDOOR_FEATURE_COLUMNS)
        X = pd.concat([base_X, synth_X], ignore_index=True)
        y = np.concatenate([base_y, np.array(synth_labels)])
    else:
        X = base_X.copy()
        y = base_y.copy()

    return X, y


def train_indoor_model(n_samples: int = 1000, test_size: float = 0.2) -> Dict:
    """Train indoor room model and persist it."""
    logger.info("Starting indoor model training...")
    X, y = generate_indoor_training_data(n_samples)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=42,
    )

    model = RandomForestRegressor(
        n_estimators=160,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mse = float(mean_squared_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({"model": model, "feature_names": INDOOR_FEATURE_COLUMNS}, MODEL_PATH)

    logger.info("Indoor model training complete. MSE: %.2f, R2: %.3f", mse, r2)

    return {
        "mse": mse,
        "r2": r2,
        "n_samples": int(len(X)),
        "feature_names": INDOOR_FEATURE_COLUMNS,
        "model_path": MODEL_PATH,
    }


def load_indoor_model() -> Optional[Tuple[RandomForestRegressor, List[str]]]:
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        data = joblib.load(MODEL_PATH)
        return data["model"], data["feature_names"]
    except Exception as exc:
        logger.warning("Failed to load indoor model: %s", exc)
        return None


def predict_indoor_score(features: Dict) -> Optional[Dict]:
    model_data = load_indoor_model()
    if model_data is None:
        train_indoor_model(n_samples=1200)
        model_data = load_indoor_model()
        if model_data is None:
            return None

    model, feature_names = model_data
    vector = np.array([float(features.get(name, 0.0)) for name in feature_names]).reshape(1, -1)
    prediction = float(np.clip(model.predict(vector)[0], 0.0, 100.0))

    return {
        "ai_score": prediction,
        "feature_importance": {
            name: float(value)
            for name, value in sorted(
                zip(feature_names, model.feature_importances_),
                key=lambda x: x[1],
                reverse=True,
            )
        },
    }
