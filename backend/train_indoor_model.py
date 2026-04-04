"""Train indoor feng shui model."""

import logging

from indoor_ai_model import train_indoor_model


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


if __name__ == "__main__":
    print("=" * 60)
    print("Training Indoor Feng Shui AI Model")
    print("=" * 60)

    metrics = train_indoor_model(n_samples=1200, test_size=0.2)

    print("\n" + "=" * 60)
    print("Indoor Training Complete")
    print("=" * 60)
    print(f"Mean Squared Error: {metrics['mse']:.2f}")
    print(f"R2 Score: {metrics['r2']:.3f}")
    print(f"Number of samples: {metrics['n_samples']}")
    print(f"Model saved to: {metrics['model_path']}")
    print("=" * 60)
