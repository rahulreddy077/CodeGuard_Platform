"""
CodeGuard - AI Detector Model Training Script
==============================================
Trains the unified AI detection pipeline on all manifest samples.
Selects the decision threshold from out-of-fold GroupKFold predictions.
Saves {pipeline, threshold, training_manifest_hash, date} with joblib to models/ai_detector.joblib.
"""

import os
import sys
import glob
import hashlib
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import GroupKFold
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score

from modules.ai_detection.model import build_pipeline


def generate_manifest_if_missing(manifest_path: str = "datasets/ai_dataset_manifest.csv") -> pd.DataFrame:
    """Creates the dataset manifest CSV if it does not exist."""
    if os.path.exists(manifest_path):
        return pd.read_csv(manifest_path)

    sol_dir = os.path.join("datasets", "obfuscated_pairs", "solutions")
    ai_dir = os.path.join("datasets", "obfuscated_pairs", "ai_generated")

    sol_files = sorted(glob.glob(os.path.join(sol_dir, "*.py")))
    ai_files = sorted(glob.glob(os.path.join(ai_dir, "*.py")))

    rows = []
    for fpath in sol_files:
        pname = os.path.basename(fpath).replace(".py", "")
        # Standardize path separators
        norm_path = fpath.replace("\\", "/")
        rows.append({
            "path": norm_path,
            "problem_id": pname,
            "label": 0,
            "generator": "human",
            "author": "human"
        })

    for fpath in ai_files:
        pname = os.path.basename(fpath).replace(".py", "")
        norm_path = fpath.replace("\\", "/")
        rows.append({
            "path": norm_path,
            "problem_id": pname,
            "label": 1,
            "generator": "codellama",
            "author": "codellama"
        })

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    df.to_csv(manifest_path, index=False)
    print(f"Generated training manifest CSV at {manifest_path} ({len(df)} samples)")
    return df


def train_and_save(manifest_path: str = "datasets/ai_dataset_manifest.csv", model_output_path: str = "models/ai_detector.joblib"):
    df = generate_manifest_if_missing(manifest_path)

    # Compute manifest file hash
    with open(manifest_path, "rb") as f:
        manifest_hash = hashlib.sha256(f.read()).hexdigest()

    # Load code contents
    codes = []
    for _, row in df.iterrows():
        p = row["path"]
        if not os.path.exists(p):
            # Fallback to local path separator
            p = p.replace("/", os.sep)
        with open(p, "r", encoding="utf-8") as f:
            codes.append(f.read())
    
    df["code"] = codes
    y = df["label"].values
    groups = df["problem_id"].values

    print(f"Loaded {len(df)} total dataset samples ({sum(y)} AI, {len(y)-sum(y)} Human).")

    # GroupKFold to select optimal threshold from Out-Of-Fold predictions
    gkf = GroupKFold(n_splits=5)
    oof_probs = np.zeros(len(df))

    for train_idx, test_idx in gkf.split(codes, y, groups=groups):
        train_codes = [codes[i] for i in train_idx]
        test_codes = [codes[i] for i in test_idx]
        train_y = y[train_idx]

        pipe = build_pipeline()
        pipe.fit(train_codes, train_y)
        oof_probs[test_idx] = pipe.predict_proba(test_codes)[:, 1]

    # Select threshold: FPR <= 0.25 constraint, then maximize F1
    # This documented objective ensures at most 1 in 4 human submissions
    # are flagged for review, while maximizing detection performance.
    best_thresh = 0.50
    best_f1 = -1.0
    best_prec = 0.0
    best_rec = 0.0

    threshold_candidates = np.linspace(0.10, 0.90, 81)
    for t in threshold_candidates:
        preds = (oof_probs >= t).astype(int)
        f1 = f1_score(y, preds, zero_division=0)
        prec = precision_score(y, preds, zero_division=0)
        rec = recall_score(y, preds, zero_division=0)
        # Compute FPR on human samples
        human_mask = (y == 0)
        fp = int(np.sum(preds[human_mask] == 1))
        tn = int(np.sum(preds[human_mask] == 0))
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 1.0

        # Only consider thresholds meeting FPR constraint
        if fpr <= 0.25 and f1 > best_f1:
            best_f1 = f1
            best_thresh = round(float(t), 4)
            best_prec = prec
            best_rec = rec

    # If no threshold meets FPR <= 0.25, fall back to max-F1 unconstrained
    if best_f1 <= 0:
        for t in threshold_candidates:
            preds = (oof_probs >= t).astype(int)
            f1 = f1_score(y, preds, zero_division=0)
            if f1 > best_f1:
                best_f1 = f1
                best_thresh = round(float(t), 4)
                best_prec = precision_score(y, preds, zero_division=0)
                best_rec = recall_score(y, preds, zero_division=0)
        print(f"WARNING: No threshold achieves FPR <= 0.25. Fell back to max-F1.")

    auc = roc_auc_score(y, oof_probs)
    print(f"Optimal Out-Of-Fold Threshold Selected: {best_thresh}")
    print(f"  Selection Objective: FPR <= 0.25, then max F1")
    print(f"  OOF Precision: {best_prec:.4f}")
    print(f"  OOF Recall:    {best_rec:.4f}")
    print(f"  OOF F1-Score:  {best_f1:.4f}")
    print(f"  OOF ROC-AUC:   {auc:.4f}")

    # Fit final pipeline on ALL training samples
    final_pipeline = build_pipeline()
    final_pipeline.fit(codes, y)

    payload = {
        "pipeline": final_pipeline,
        "threshold": best_thresh,
        "training_manifest_hash": manifest_hash,
        "date": datetime.now(timezone.utc).isoformat()
    }

    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    joblib.dump(payload, model_output_path)
    print(f"Successfully saved trained AI detector artifact to {model_output_path}")

    return payload


if __name__ == "__main__":
    train_and_save()
