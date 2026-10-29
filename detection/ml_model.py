"""
Machine Learning Behavioral Classifier for Ransomware Detection Simulator.
Uses Scikit-Learn to train and evaluate an explainable Random Forest / Decision Tree model
on synthetic behavioral telemetry.
"""

import numpy as np
import logging

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.tree import DecisionTreeClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "events_per_sec",
    "rename_rate",
    "ext_change_ratio",
    "mod_burst_rate",
    "unique_ext_count"
]


class RansomwareMLClassifier:
    """
    Supervised machine learning model trained on synthetic behavioral profiles.
    Used for educational demonstration of AI-driven cybersecurity detection.
    """
    def __init__(self):
        self.is_trained = False
        self.model = None
        self.feature_importances = {}
        self.training_sample_count = 0
        if SKLEARN_AVAILABLE:
            self._train_initial_model()

    def _generate_synthetic_dataset(self, n_samples: int = 1200):
        """
        Synthesizes realistic training distributions for benign and ransomware-like behavioral telemetry.
        """
        np.random.seed(42)
        n_benign = n_samples // 2
        n_ransom = n_samples - n_benign

        # Benign Profiles: Lower velocity, minimal renames, no suspicious extension tampering
        benign_events_per_sec = np.random.exponential(scale=1.2, size=n_benign).clip(0.1, 4.0)
        benign_rename_rate = np.random.beta(a=1, b=8, size=n_benign) * 1.5
        benign_ext_ratio = np.zeros(n_benign)  # Benign rarely changes extensions to .locked/.crypto
        benign_mod_rate = np.random.exponential(scale=0.8, size=n_benign).clip(0.0, 3.5)
        benign_unique_ext = np.random.choice([1, 2, 3], size=n_benign, p=[0.7, 0.25, 0.05])

        X_benign = np.column_stack([
            benign_events_per_sec,
            benign_rename_rate,
            benign_ext_ratio,
            benign_mod_rate,
            benign_unique_ext
        ])
        y_benign = np.zeros(n_benign, dtype=int)

        # Ransomware Profiles: High velocity bursts, high rename rates, high extension tampering
        ransom_events_per_sec = np.random.normal(loc=8.5, scale=3.0, size=n_ransom).clip(3.5, 25.0)
        ransom_rename_rate = np.random.normal(loc=6.0, scale=2.5, size=n_ransom).clip(2.0, 20.0)
        ransom_ext_ratio = np.random.uniform(low=0.4, high=1.0, size=n_ransom)
        ransom_mod_rate = np.random.normal(loc=7.0, scale=2.5, size=n_ransom).clip(2.5, 18.0)
        ransom_unique_ext = np.random.choice([2, 3, 4, 5], size=n_ransom, p=[0.2, 0.4, 0.3, 0.1])

        X_ransom = np.column_stack([
            ransom_events_per_sec,
            ransom_rename_rate,
            ransom_ext_ratio,
            ransom_mod_rate,
            ransom_unique_ext
        ])
        y_ransom = np.ones(n_ransom, dtype=int)

        X = np.vstack([X_benign, X_ransom])
        y = np.concatenate([y_benign, y_ransom])

        # Shuffle dataset
        indices = np.arange(len(y))
        np.random.shuffle(indices)
        return X[indices], y[indices]

    def _train_initial_model(self):
        """Trains the Random Forest model on the synthetic behavioral dataset."""
        try:
            X, y = self._generate_synthetic_dataset(1500)
            self.model = RandomForestClassifier(
                n_estimators=40,
                max_depth=6,
                random_state=42,
                class_weight="balanced"
            )
            self.model.fit(X, y)
            self.is_trained = True
            self.training_sample_count = len(y)

            # Store feature importances for transparency and presentation
            importances = self.model.feature_importances_
            self.feature_importances = {
                name: round(float(imp) * 100, 2)
                for name, imp in zip(FEATURE_NAMES, importances)
            }
        except Exception as e:
            logger.error(f"Error training synthetic ML model: {e}")
            self.is_trained = False

    def predict(self, metrics: dict) -> dict:
        """
        Classifies current behavioral metrics as Benign or Ransomware-like.
        Returns prediction, probability confidence, and explanatory attribution.
        """
        if not SKLEARN_AVAILABLE or not self.is_trained or self.model is None:
            return {
                "enabled": False,
                "prediction": "ML Disabled / Unavailable",
                "is_ransomware": False,
                "confidence": 0.0,
                "top_features": [],
                "disclaimer": "Machine Learning module is disabled or Scikit-learn is not available."
            }

        # Extract features
        events_per_sec = float(metrics.get("velocity", 0.0))
        renames_count = float(metrics.get("renames_count", 0))
        duration = max(0.5, float(metrics.get("window_duration", 5.0)))
        rename_rate = renames_count / duration
        suspicious_ext = float(metrics.get("suspicious_ext_count", 0))
        total_events = max(1.0, float(metrics.get("total_events", 1)))
        ext_change_ratio = min(1.0, suspicious_ext / total_events)
        mod_rate = float(metrics.get("modifications_count", 0)) / duration
        unique_ext_count = float(metrics.get("unique_extensions", 1))

        feature_vector = np.array([[
            events_per_sec,
            rename_rate,
            ext_change_ratio,
            mod_rate,
            unique_ext_count
        ]])

        try:
            probs = self.model.predict_proba(feature_vector)[0]
            # probs[0] = Benign, probs[1] = Ransomware
            ransom_prob = float(probs[1]) if len(probs) > 1 else 0.0
            is_ransom = ransom_prob >= 0.50
            confidence = round(max(ransom_prob, 1.0 - ransom_prob) * 100, 1)

            sorted_features = sorted(self.feature_importances.items(), key=lambda x: x[1], reverse=True)

            return {
                "enabled": True,
                "prediction": "Ransomware-like Anomaly" if is_ransom else "Benign Behavior",
                "is_ransomware": is_ransom,
                "confidence": confidence,
                "ransom_probability": round(ransom_prob * 100, 1),
                "feature_vector": {
                    "events_per_sec": round(events_per_sec, 2),
                    "rename_rate": round(rename_rate, 2),
                    "ext_change_ratio": round(ext_change_ratio, 2),
                    "mod_burst_rate": round(mod_rate, 2),
                    "unique_ext_count": int(unique_ext_count)
                },
                "feature_importances": self.feature_importances,
                "top_features": sorted_features[:3],
                "disclaimer": "Model trained on synthetic behavioral data for educational demonstration. Not validated for production protection."
            }
        except Exception as e:
            logger.error(f"Prediction error in ML model: {e}")
            return {
                "enabled": False,
                "error": str(e),
                "prediction": "Error in ML prediction",
                "is_ransomware": False,
                "confidence": 0.0
            }


# Global singleton instance
ml_classifier = RansomwareMLClassifier()
