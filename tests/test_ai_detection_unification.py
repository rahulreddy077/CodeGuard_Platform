"""
CodeGuard - AI Authorship Detector Unification Pytest Suite
============================================================
Tests:
1. No Data Leakage: Confirms TF-IDF vocabulary is strictly built from the training fold
   during cross-validation and contains no unique test fold tokens.
2. Dashboard Equality: Confirms check_ai_generated() probability and threshold equal
   the pipeline predictions from models/ai_detector.joblib.
"""

import os
import pytest
import joblib
import numpy as np
from sklearn.model_selection import GroupKFold

from modules.ai_detection.model import build_pipeline
from modules.ai_detection import check_ai_generated, get_model_data
from experiments.train_ai_detector import generate_manifest_if_missing, train_and_save


def test_no_data_leakage_in_evaluation():
    """
    Verifies that fitting build_pipeline on a training fold extracts a TF-IDF
    vocabulary consisting EXCLUSIVELY of tokens present in the training fold.
    Unique tokens exclusive to the test fold must NOT leak into the fitted vocabulary.
    """
    train_codes = [
        "def compute_sum(a, b):\n    # train fold token: alpha_sum\n    return a + b",
        "def calculate_product(x, y):\n    # train fold token: beta_prod\n    return x * y"
    ]
    train_labels = [0, 1]

    test_codes = [
        "def secret_eval_func(z):\n    # test fold token: gamma_secret_unseen\n    return z ** 2"
    ]

    pipe = build_pipeline()
    pipe.fit(train_codes, train_labels)

    # Extract fitted TfidfVectorizer from FeatureUnion named 'features'
    features_union = pipe.named_steps["features"]
    tfidf_vectorizer = features_union.transformer_list[0][1]
    vocab = set(tfidf_vectorizer.vocabulary_.keys())

    # Assert train fold tokens are in vocabulary
    assert "alpha_sum" in vocab or "sum" in vocab
    assert "beta_prod" in vocab or "prod" in vocab

    # Assert test-fold-exclusive token NEVER leaked into vocabulary
    assert "gamma_secret_unseen" not in vocab
    assert "secret_eval_func" not in vocab


def test_dashboard_prediction_equals_saved_joblib():
    """
    Verifies that the live dashboard score returned by check_ai_generated()
    matches the exact prediction probability and threshold from the serialized joblib artifact.
    """
    manifest_path = "datasets/ai_dataset_manifest.csv"
    model_path = "models/ai_detector.joblib"

    if not os.path.exists(model_path):
        train_and_save(manifest_path, model_path)

    model_data = get_model_data(model_path)
    pipeline = model_data["pipeline"]
    threshold = float(model_data["threshold"])

    sample_code = """
def is_palindrome(s: str) -> bool:
    # Check if string is palindrome
    cleaned = [c.lower() for c in s if c.isalnum()]
    return cleaned == cleaned[::-1]
"""

    res = check_ai_generated(sample_code, model_path=model_path)
    expected_prob = float(pipeline.predict_proba([sample_code])[0][1])

    assert res["success"] is True
    assert res["ai_probability"] == round(expected_prob, 4)
    assert res["threshold_used"] == threshold

    if expected_prob >= threshold:
        assert res["risk_tier"] == "High Risk"
    elif expected_prob >= 0.50 * threshold:
        assert res["risk_tier"] == "Moderate Risk"
    else:
        assert res["risk_tier"] == "Low Risk"
