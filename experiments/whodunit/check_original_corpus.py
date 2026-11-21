import os
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)

sys.path.insert(0, os.path.abspath("."))
from modules.ai_detection.model import build_pipeline
from experiments.train_ai_detector import generate_manifest_if_missing

df = generate_manifest_if_missing("datasets/ai_dataset_manifest.csv")
codes = []
for _, row in df.iterrows():
    p = row["path"].replace("/", os.sep)
    with open(p, encoding="utf-8") as f:
        codes.append(f.read())
y = df["label"].values
groups = df["problem_id"].values

gkf = GroupKFold(n_splits=5)
oof_probs = np.zeros(len(codes))
fold_aucs = []

for fold, (tr_idx, te_idx) in enumerate(gkf.split(codes, y, groups=groups)):
    tr_c = [codes[i] for i in tr_idx]
    tr_y = y[tr_idx]
    te_c = [codes[i] for i in te_idx]
    te_y = y[te_idx]

    pipe = build_pipeline()
    pipe.fit(tr_c, tr_y)
    probs = pipe.predict_proba(te_c)[:, 1]
    oof_probs[te_idx] = probs

    # per fold auc
    try:
        f_auc = roc_auc_score(te_y, probs)
        fold_aucs.append(f_auc)
    except Exception as e:
        print(f"Fold {fold} AUC error:", e)

pooled_auc = roc_auc_score(y, oof_probs)
mean_fold_auc = np.mean(fold_aucs)

print("=" * 50)
print("70-FILE ORIGINAL CORPUS EVALUATION")
print("=" * 50)
print(f"Pooled OOF ROC-AUC:   {pooled_auc:.4f}")
print(f"Mean-of-folds ROC-AUC: {mean_fold_auc:.4f}")
print("Per-fold AUCs:", [round(a, 4) for a in fold_aucs])

# Metrics at threshold 0.54
preds_54 = (oof_probs >= 0.54).astype(int)
print(f"\nAt threshold 0.54:")
print(f"Accuracy:  {accuracy_score(y, preds_54):.4f}")
print(f"Precision: {precision_score(y, preds_54, zero_division=0):.4f}")
print(f"Recall:    {recall_score(y, preds_54, zero_division=0):.4f}")
print(f"F1:        {f1_score(y, preds_54, zero_division=0):.4f}")
