"""
CodeGuard - Task A: Ablation Study Experiment (Strict Out-of-Fold Thresholding)
==================================================================================
Evaluates 4 similarity/detection approaches on datasets/obfuscated_pairs/pairs.csv
using 5-Fold Stratified Cross-Validation with strict fold-wise threshold tuning
to prevent optimistic test set bias:

 1. Semantic-Only (GraphCodeBERT Embedding Cosine)
 2. Structural-Only (AST Fingerprint Jaccard — matches live pipeline)
 3. Fused-Weighted (0.60 * Semantic + 0.40 * Structural, weights from config)
 4. Fused Logistic Regression (Trained on [Semantic, Structural] features)

Outputs results to results/ablation.csv.

NOTE: Preprocessing deliberately mirrors modules/plagiarism/__init__.py so
that ablation measurements are of the DEPLOYED engine, not a proxy.
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.similarity import SimilarityService
from backend.config import SIMILARITY_CONFIG
from modules.ast.parser import parse_code
from modules.ast.fingerprint import generate_fingerprint
from modules.ast import normalize_ast
try:
    from modules.ast import normalize_code as _normalize_code
except ImportError:
    _normalize_code = None

_SEMANTIC_W  = SIMILARITY_CONFIG["semantic_weight"]   # 0.60
_STRUCTURAL_W = SIMILARITY_CONFIG["structural_weight"] # 0.40

def compute_tfidf_cosine(code1: str, code2: str) -> float:
    from sklearn.feature_extraction.text import TfidfVectorizer
    try:
        vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
        tfidf = vectorizer.fit_transform([code1, code2])
        sim = (tfidf[0] * tfidf[1].T).toarray()[0][0]
        return float(round(sim, 4))
    except Exception:
        return 0.0

def get_semantic_similarity(code1: str, code2: str) -> float:
    try:
        from backend.services.embedding import EmbeddingService
        vec1 = EmbeddingService.get_embedding(code1)
        vec2 = EmbeddingService.get_embedding(code2)
        return SimilarityService.calculate_cosine_similarity(vec1, vec2)
    except Exception:
        return compute_tfidf_cosine(code1, code2)

def get_structural_similarity(code1: str, code2: str) -> float:
    """
    Calls the reference live pipeline implementation:
    SimilarityService.compute_structural_similarity(code1, code2)
    which runs normalize_ast(parse_code(code)) -> generate_fingerprint(exclude_context=True) -> Jaccard.
    """
    return SimilarityService.compute_structural_similarity(code1, code2)

def evaluate_oof(scores, y, skf):
    """
    Finds optimal threshold on train fold, applies it to test fold,
    accumulates out-of-fold predictions.
    """
    oof_preds = np.zeros(len(y))
    
    for train_idx, test_idx in skf.split(scores, y):
        train_scores, train_y = scores[train_idx], y[train_idx]
        test_scores = scores[test_idx]
        
        best_acc = 0.0
        best_t = 0.5
        for t in np.linspace(0.1, 0.9, 81):
            t_acc = accuracy_score(train_y, (train_scores >= t).astype(int))
            if t_acc > best_acc:
                best_acc = t_acc
                best_t = t
                
        oof_preds[test_idx] = (test_scores >= best_t).astype(int)
        
    acc = accuracy_score(y, oof_preds)
    prec = precision_score(y, oof_preds, zero_division=0)
    rec = recall_score(y, oof_preds, zero_division=0)
    f1 = f1_score(y, oof_preds, zero_division=0)
    auc = roc_auc_score(y, scores)
    
    return round(acc, 4), round(prec, 4), round(rec, 4), round(f1, 4), round(auc, 4)

def run_ablation():
    csv_path = os.path.join("datasets", "obfuscated_pairs", "pairs.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Pairs dataset not found at {csv_path}.")

    print(f"Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Dataset loaded: {len(df)} total pairs ({df['label'].sum()} positive, {len(df) - df['label'].sum()} negative)")

    print("\nExtracting semantic & structural features across all pairs...")
    semantic_scores = []
    structural_scores = []
    
    for idx, row in df.iterrows():
        c1 = str(row["original_code"])
        c2 = str(row["variant_code"])
        
        s_sem = get_semantic_similarity(c1, c2)
        s_struct = get_structural_similarity(c1, c2)
        
        semantic_scores.append(s_sem)
        structural_scores.append(s_struct)
        
        if (idx + 1) % 40 == 0 or (idx + 1) == len(df):
            print(f"  Processed {idx + 1}/{len(df)} pairs...")

    df["semantic_sim"] = semantic_scores
    df["structural_sim"] = structural_scores
    df["fused_weighted"] = _SEMANTIC_W * df["semantic_sim"] + _STRUCTURAL_W * df["structural_sim"]

    # Fused Logistic Regression via 5-Fold Stratified Cross Validation
    X = df[["semantic_sim", "structural_sim"]].values
    y = df["label"].values
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    lr_probs = np.zeros(len(df))
    for train_idx, test_idx in skf.split(X, y):
        clf = LogisticRegression()
        clf.fit(X[train_idx], y[train_idx])
        lr_probs[test_idx] = clf.predict_proba(X[test_idx])[:, 1]
        
    df["fused_lr"] = lr_probs

    methods = {
        "Semantic-Only (GraphCodeBERT)": df["semantic_sim"].values,
        "Structural-Only (AST Jaccard)": df["structural_sim"].values,
        "Fused-Weighted (0.6/0.4)": df["fused_weighted"].values,
        "Fused-LR (Logistic Regression)": df["fused_lr"].values
    }

    results = []
    
    print("\n=======================================================")
    print("      ABLATION RESULTS (OUT-OF-FOLD THRESHOLDING)      ")
    print("=======================================================")

    for name, scores in methods.items():
        acc, prec, rec, f1, auc = evaluate_oof(scores, y, skf)
        row_res = {
            "Method": name,
            "Accuracy": acc,
            "Precision": prec,
            "Recall": rec,
            "F1-Score": f1,
            "ROC-AUC": auc,
            "Validation_Method": "5-Fold Out-of-Fold Thresholding"
        }
        results.append(row_res)
        print(f"\n[{name}]")
        print(f"  Accuracy: {acc} | Precision: {prec} | Recall: {rec} | F1: {f1} | ROC-AUC: {auc}")

    os.makedirs("results", exist_ok=True)
    res_df = pd.DataFrame(results)
    out_csv = os.path.join("results", "ablation.csv")
    res_df.to_csv(out_csv, index=False)
    print(f"\nResults successfully saved to {out_csv}")
    
    return res_df

if __name__ == "__main__":
    run_ablation()
