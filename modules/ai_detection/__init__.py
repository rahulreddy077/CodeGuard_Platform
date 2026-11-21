"""
CodeGuard - AI Code Detection Classifier
==========================================
Uses unified sklearn Pipeline (TF-IDF + Heuristic FeatureUnion + Logistic Regression)
loaded from models/ai_detector.joblib trained on the manifest dataset.

Review Prioritization Tiers:
- Flagged for Review (High Pattern Overlap): Probability >= Threshold
- Optional Review (Moderate Pattern Overlap): 0.5 * Threshold <= Probability < Threshold
- Routine Structure (Low Pattern Overlap): Probability < 0.5 * Threshold

Disclaimer:
AI detection probability scores are decision-support indicators designed for faculty review prioritization.
They do not constitute automated evidence or proof of academic dishonesty.
"""

import os
import re
import math
import joblib
from modules.quality import validate_python_code
from modules.ai_detection.model import compute_shannon_entropy, CodeHeuristicExtractor, build_pipeline

_MODEL_CACHE = None
DEFAULT_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "ai_detector.joblib"))


def get_model_data(model_path: str = DEFAULT_MODEL_PATH) -> dict:
    """
    Loads and caches the trained AI detector pipeline artifact.
    If the artifact is missing, invokes training script to build it on-demand.
    """
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    if not os.path.exists(model_path):
        from experiments.train_ai_detector import train_and_save
        _MODEL_CACHE = train_and_save(model_output_path=model_path)
    else:
        _MODEL_CACHE = joblib.load(model_path)

    return _MODEL_CACHE


def check_ai_generated(code: str, model_path: str = DEFAULT_MODEL_PATH) -> dict:
    """
    Analyzes Python code to predict the probability that it exhibits AI generation patterns.
    Uses the unified trained Pipeline and decision threshold from models/ai_detector.joblib.

    Returns probability, decision threshold, review tier, confidence score, and explanatory heuristics.
    """
    valid, err_msg = validate_python_code(code)
    if not valid:
        return {
            "success": False,
            "error": err_msg
        }

    model_data = get_model_data(model_path)
    pipeline = model_data["pipeline"]
    threshold = float(model_data["threshold"])

    length = len(code)
    entropy = compute_shannon_entropy(code)
    has_docstring = '"""' in code or "'''" in code
    has_type_hints = bool(re.search(r":\s*(int|str|float|list|dict|bool|Any)\b", code)) or "->" in code
    has_comments = "#" in code
    lines = code.splitlines()
    total_lines = float(len(lines))
    avg_line_length = length / max(1.0, total_lines)

    snake_case_count = len(re.findall(r"\b[a-z]+_[a-z0-9_]+\b", code))
    camel_case_count = len(re.findall(r"\b[a-z]+[A-Z][a-zA-Z0-9]*\b", code))

    # Predict probability directly from the unified pipeline
    try:
        prob_ml = float(pipeline.predict_proba([code])[0][1])
    except Exception:
        prob_ml = 0.5

    prob_ml = round(prob_ml, 4)

    # Decision-Support Review Prioritization Tiers (derived from evaluated threshold)
    if prob_ml >= threshold:
        review_tier = "Flagged for Faculty Review"
        legacy_tier = "High Risk"
    elif prob_ml >= 0.50 * threshold:
        review_tier = "Optional Review"
        legacy_tier = "Moderate Risk"
    else:
        review_tier = "Routine Code Structure"
        legacy_tier = "Low Risk"

    return {
        "success": True,
        "ai_probability": prob_ml,
        "threshold_used": threshold,
        "risk_tier": legacy_tier,
        "review_tier": review_tier,
        "disclaimer": "AI detection probability scores are decision-support indicators for faculty review prioritization, not automated verdicts.",
        "confidence": 0.85 if length > 100 else 0.60,
        "heuristics": {
            "tfidf_classifier_score": prob_ml,
            "token_entropy_score": round(min(entropy / 6.0, 1.0), 4),
            "docstring_formatting_score": 0.85 if has_docstring else 0.05,
            "type_hint_density_score": 0.80 if has_type_hints else 0.05,
            "comment_density_score": 0.70 if has_comments else 0.05,
            "has_docstring": has_docstring,
            "has_type_hints": has_type_hints,
            "has_comments": has_comments,
            "entropy": entropy,
            "length_chars": length,
            "avg_line_length": round(avg_line_length, 2),
            "snake_case_count": snake_case_count,
            "camel_case_count": camel_case_count
        }
    }
