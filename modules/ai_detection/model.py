"""
CodeGuard - AI Code Detection Model & Feature Engineering Pipeline
===================================================================
Defines the unified sklearn Pipeline and custom heuristic feature extractor.
Used identically across training, cross-validation evaluation, and live dashboard inference.
"""

import math
import re
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline


def compute_shannon_entropy(code: str) -> float:
    """Computes character-level Shannon entropy for code text."""
    if not code:
        return 0.0
    probs = [code.count(c) / len(code) for c in set(code)]
    return float(round(-sum(p * math.log2(p) for p in probs if p > 0), 4))


class CodeHeuristicExtractor(BaseEstimator, TransformerMixin):
    """
    Custom scikit-learn transformer extracting code structure heuristics:
    - Shannon entropy
    - Comment presence and density
    - Line-length statistics (avg line length, max line length, total lines, total chars)
    - Naming style & typing features (type hints, snake_case, camelCase, PascalCase counts)

    Note: Docstring presence/density is excluded per requirement as it is constant zero in current dataset.
    """

    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        features = []
        for sample in X:
            code = sample if isinstance(sample, str) else str(sample)
            lines = code.splitlines()
            total_lines = float(len(lines))
            char_count = float(len(code))

            entropy = compute_shannon_entropy(code)
            has_comments = 1.0 if "#" in code else 0.0
            comment_lines = sum(1 for line in lines if "#" in line)
            comment_density = comment_lines / max(1.0, total_lines)

            avg_line_length = char_count / max(1.0, total_lines)
            max_line_length = float(max([len(l) for l in lines], default=0))

            has_type_hints = 1.0 if (bool(re.search(r":\s*(int|str|float|list|dict|bool|Any)\b", code)) or "->" in code) else 0.0
            snake_case_count = float(len(re.findall(r"\b[a-z]+_[a-z0-9_]+\b", code)))
            camel_case_count = float(len(re.findall(r"\b[a-z]+[A-Z][a-zA-Z0-9]*\b", code)))
            pascal_case_count = float(len(re.findall(r"\b[A-Z][a-z0-9]+[A-Z][a-zA-Z0-9]*\b", code)))

            row = [
                entropy,
                has_comments,
                comment_density,
                avg_line_length,
                max_line_length,
                total_lines,
                char_count,
                has_type_hints,
                snake_case_count,
                camel_case_count,
                pascal_case_count
            ]
            features.append(row)
        return np.array(features, dtype=np.float64)

    def get_feature_names_out(self, input_features=None):
        return np.array([
            "entropy",
            "has_comments",
            "comment_density",
            "avg_line_length",
            "max_line_length",
            "total_lines",
            "char_count",
            "has_type_hints",
            "snake_case_count",
            "camel_case_count",
            "pascal_case_count"
        ])


def build_pipeline(C: float = 1.0, max_iter: int = 1000, random_state: int = 42) -> Pipeline:
    """
    Constructs the unified AI detection sklearn Pipeline:
    - FeatureUnion of TF-IDF word vectorizer and CodeHeuristicExtractor
    - LogisticRegression with class_weight='balanced'
    """
    return Pipeline([
        ("features", FeatureUnion([
            ("tfidf", TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")),
            ("heuristics", CodeHeuristicExtractor())
        ])),
        ("classifier", LogisticRegression(class_weight="balanced", C=C, max_iter=max_iter, random_state=random_state))
    ])
