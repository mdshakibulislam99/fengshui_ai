# Script to train the Random Forest model

import logging
from ai_model import train_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == '__main__':
    print("=" * 60)
    print("Training Feng Shui Random Forest Model")
    print("=" * 60)
    
    # Train the model with 2000 samples
    metrics = train_model(n_samples=2000, test_size=0.2)
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"Mean Squared Error: {metrics['mse']:.2f}")
    print(f"R² Score: {metrics['r2']:.3f}")
    print(f"Number of samples: {metrics['n_samples']}")
    print(f"Model saved to: {metrics['model_path']}")
    print(f"Features: {', '.join(metrics['feature_names'])}")
    print("=" * 60)
