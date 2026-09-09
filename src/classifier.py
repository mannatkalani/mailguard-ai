"""
Loads the serialized production model + vectorizer and exposes a simple
classification API. This is the lean, single-model version — no model
switching, to keep the app focused on the Gmail workflow.
"""

import json
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd

from src.preprocessing import clean_text

ROOT = Path(__file__).parent.parent
MODELS_DIR = ROOT / "models"


class SpamClassifier:
    def __init__(self):
        self.model = joblib.load(MODELS_DIR / "model.joblib")
        self.vectorizer = joblib.load(MODELS_DIR / "vectorizer.joblib")
        with open(MODELS_DIR / "metadata.json") as f:
            self.metadata = json.load(f)
        self.model_name = self.metadata["production_model"]

    def predict_batch(self, texts: Iterable[str]) -> pd.DataFrame:
        texts = list(texts)
        cleaned = [clean_text(t) for t in texts]
        vecs = self.vectorizer.transform(cleaned)
        spam_prob = self.model.predict_proba(vecs)[:, 1]
        preds = (spam_prob >= 0.5).astype(int)
        confidence = np.where(preds == 1, spam_prob, 1 - spam_prob) * 100

        return pd.DataFrame(
            {
                "clean_text": cleaned,
                "prediction": np.where(preds == 1, "SPAM", "HAM"),
                "spam_probability": spam_prob,
                "confidence": confidence,
            }
        )

    def predict_one(self, text: str) -> dict:
        df = self.predict_batch([text])
        row = df.iloc[0]
        return {
            "prediction": row["prediction"],
            "spam_probability": float(row["spam_probability"]),
            "confidence": float(row["confidence"]),
            "clean_text": row["clean_text"],
        }

    def apply_review_threshold(self, df: pd.DataFrame, threshold: float) -> pd.DataFrame:
        df = df.copy()
        df["status"] = np.where(df["confidence"] < threshold, "REVIEW", df["prediction"])
        return df

    def top_features_for_text(self, clean_text_str: str, top_n: int = 8) -> list:
        """Which tokens in this message most influenced the decision (linear models only)."""
        if not hasattr(self.model, "coef_"):
            return []
        vocab = self.vectorizer.get_feature_names_out()
        vec = self.vectorizer.transform([clean_text_str])
        indices = vec.nonzero()[1]
        if len(indices) == 0:
            return []
        coefs = self.model.coef_[0]
        contributions = [(vocab[i], float(coefs[i])) for i in indices]
        contributions.sort(key=lambda x: abs(x[1]), reverse=True)
        return contributions[:top_n]


_classifier_instance = None


def get_classifier() -> SpamClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = SpamClassifier()
    return _classifier_instance
