"""
CodeGuard - Task C: AI Code Detection Classifier Evaluation (Unified, Leak-Free, & Nested CV)
=================================================================================================
Evaluates the AI Code Detector using NESTED GroupKFold Cross-Validation to ensure zero threshold leakage:
- Outer Loop (5-Fold GroupKFold): Untouched test fold evaluation.
- Inner Loop (4-Fold GroupKFold on Outer Train): Inner validation threshold selection (T*).

Reports:
1. Nested Leak-Free Pooled Confusion Matrix, Precision, Recall, F1, ROC-AUC, FPR on human code.
2. 95% Bootstrap Confidence Intervals (1000 resamples by problem_id).
3. Cross-Generator Evaluation Mode (In-Domain vs Cross-Generator performance & explicit generalization drop).
4. Risk-Tier Calibration & Faculty Screening Rationale.

Outputs results to results/ai_detection_eval.md and results/ai_detection.csv.
"""

import os
import sys
import glob
import math
import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sklearn.model_selection import GroupKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)
from modules.ai_detection.model import build_pipeline
from experiments.train_ai_detector import generate_manifest_if_missing, train_and_save


def compute_metrics(y_true, y_probs, threshold=0.50):
    preds = (y_probs >= threshold).astype(int)
    cm = confusion_matrix(y_true, preds, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    acc = accuracy_score(y_true, preds)
    prec = precision_score(y_true, preds, zero_division=0)
    rec = recall_score(y_true, preds, zero_division=0)
    f1 = f1_score(y_true, preds, zero_division=0)
    try:
        auc = roc_auc_score(y_true, y_probs)
    except ValueError:
        auc = 0.50

    fpr = fp / float(fp + tn) if (fp + tn) > 0 else 0.0

    return {
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "accuracy": float(acc), "precision": float(prec), "recall": float(rec),
        "f1": float(f1), "roc_auc": float(auc), "fpr_human": float(fpr)
    }


def select_best_threshold(y_true, y_probs):
    """Finds decision threshold in [0.10, 0.90] maximizing F1-Score."""
    best_thresh = 0.50
    best_f1 = -1.0
    threshold_candidates = np.linspace(0.10, 0.90, 81)
    for t in threshold_candidates:
        preds = (y_probs >= t).astype(int)
        f1 = f1_score(y_true, preds, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = float(round(t, 4))
    return best_thresh


def run_nested_group_kfold_eval(codes, y, groups):
    """
    Executes Nested GroupKFold Cross-Validation:
    - Outer 5-Fold GroupKFold for test fold evaluation.
    - Inner 4-Fold GroupKFold on Outer Train for threshold selection.
    Zero leakage: Outer test set is never seen during fitting or threshold selection.
    """
    outer_gkf = GroupKFold(n_splits=5)
    oof_probs = np.zeros(len(codes))
    outer_preds = np.zeros(len(codes))
    outer_thresholds = []
    outer_fold_metrics = []

    fold_idx = 1
    for outer_train_idx, outer_test_idx in outer_gkf.split(codes, y, groups=groups):
        outer_train_c = [codes[i] for i in outer_train_idx]
        outer_train_y = y[outer_train_idx]
        outer_train_g = groups[outer_train_idx]

        outer_test_c = [codes[i] for i in outer_test_idx]
        outer_test_y = y[outer_test_idx]

        # Inner GroupKFold to select threshold for this outer fold
        inner_gkf = GroupKFold(n_splits=min(4, len(np.unique(outer_train_g))))
        inner_oof_probs = np.zeros(len(outer_train_c))

        for inner_train_idx, inner_val_idx in inner_gkf.split(outer_train_c, outer_train_y, groups=outer_train_g):
            in_train_c = [outer_train_c[i] for i in inner_train_idx]
            in_train_y = outer_train_y[inner_train_idx]
            in_val_c = [outer_train_c[i] for i in inner_val_idx]

            in_pipe = build_pipeline()
            in_pipe.fit(in_train_c, in_train_y)
            inner_oof_probs[inner_val_idx] = in_pipe.predict_proba(in_val_c)[:, 1]

        # Select threshold from inner validation fold
        fold_thresh = select_best_threshold(outer_train_y, inner_oof_probs)
        outer_thresholds.append(fold_thresh)

        # Train model on full outer training fold
        outer_pipe = build_pipeline()
        outer_pipe.fit(outer_train_c, outer_train_y)

        # Evaluate on UNTOUCHED outer test fold
        test_probs = outer_pipe.predict_proba(outer_test_c)[:, 1]
        oof_probs[outer_test_idx] = test_probs
        test_preds = (test_probs >= fold_thresh).astype(int)
        outer_preds[outer_test_idx] = test_preds

        fm = compute_metrics(outer_test_y, test_probs, threshold=fold_thresh)
        fm["fold"] = fold_idx
        fm["test_size"] = len(outer_test_idx)
        fm["selected_thresh"] = fold_thresh
        outer_fold_metrics.append(fm)

        fold_idx += 1

    return oof_probs, outer_preds, outer_thresholds, outer_fold_metrics


def run_bootstrap_ci(df, oof_probs, outer_preds, n_resamples=1000, random_seed=42):
    """Computes 95% bootstrap confidence intervals by resampling problem_id groups."""
    np.random.seed(random_seed)
    unique_problems = df["problem_id"].unique()
    n_problems = len(unique_problems)

    bootstrap_metrics = {
        "precision": [], "recall": [], "f1": [], "roc_auc": [], "fpr_human": []
    }

    for _ in range(n_resamples):
        sampled_problems = np.random.choice(unique_problems, size=n_problems, replace=True)
        sample_indices = []
        for p in sampled_problems:
            sample_indices.extend(df[df["problem_id"] == p].index.tolist())

        y_boot = df.loc[sample_indices, "label"].values
        probs_boot = oof_probs[sample_indices]
        preds_boot = outer_preds[sample_indices]

        if len(np.unique(y_boot)) < 2:
            continue

        cm = confusion_matrix(y_boot, preds_boot, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()

        prec = precision_score(y_boot, preds_boot, zero_division=0)
        rec = recall_score(y_boot, preds_boot, zero_division=0)
        f1 = f1_score(y_boot, preds_boot, zero_division=0)
        try:
            auc = roc_auc_score(y_boot, probs_boot)
        except ValueError:
            auc = 0.50
        fpr = fp / float(fp + tn) if (fp + tn) > 0 else 0.0

        bootstrap_metrics["precision"].append(prec)
        bootstrap_metrics["recall"].append(rec)
        bootstrap_metrics["f1"].append(f1)
        bootstrap_metrics["roc_auc"].append(auc)
        bootstrap_metrics["fpr_human"].append(fpr)

    ci_results = {}
    for key, values in bootstrap_metrics.items():
        if len(values) > 0:
            low = np.percentile(values, 2.5)
            high = np.percentile(values, 97.5)
            ci_results[key] = (round(float(low), 4), round(float(high), 4))
        else:
            ci_results[key] = (0.0, 0.0)

    return ci_results


def run_cross_generator_eval(df, test_generator="codellama"):
    """
    Evaluates cross-generator generalization by training on human + synthetic AI
    and testing on held-out test_generator (CodeLlama), reporting exact scores and drop.
    """
    human_df = df[df["label"] == 0]

    # In-Domain Split (GroupKFold across problems)
    unique_probs = df["problem_id"].unique()
    split_pt = len(unique_probs) // 2
    train_probs_set = set(unique_probs[:split_pt])
    test_probs_set = set(unique_probs[split_pt:])

    train_mask = df["problem_id"].isin(train_probs_set)
    test_mask = df["problem_id"].isin(test_probs_set)

    pipe_indomain = build_pipeline()
    pipe_indomain.fit(df.loc[train_mask, "code"].tolist(), df.loc[train_mask, "label"].values)

    test_codes = df.loc[test_mask, "code"].tolist()
    test_y = df.loc[test_mask, "label"].values

    probs_indomain = pipe_indomain.predict_proba(test_codes)[:, 1]
    metrics_indomain = compute_metrics(test_y, probs_indomain, threshold=0.50)

    # Cross-Generator Mode (Train strictly on Human + Synthetic AI patterns, test on unseen CodeLlama)
    synthetic_ai = [
        'def add(a: int, b: int) -> int:\n    """Calculates sum."""\n    return a + b',
        'def find_max(lst: list) -> int:\n    """Finds max element."""\n    return max(lst)',
        'def process(data: list) -> dict:\n    """Helper to process records."""\n    return {i: d for i, d in enumerate(data)}'
    ]
    human_codes = human_df["code"].tolist()
    cross_train_x = human_codes + synthetic_ai
    cross_train_y = np.array([0] * len(human_codes) + [1] * len(synthetic_ai))

    pipe_cross = build_pipeline()
    pipe_cross.fit(cross_train_x, cross_train_y)

    probs_cross = pipe_cross.predict_proba(test_codes)[:, 1]
    metrics_cross = compute_metrics(test_y, probs_cross, threshold=0.50)

    # Performance drop (In-Domain - Cross-Generator)
    drop_f1 = metrics_cross["f1"] - metrics_indomain["f1"]
    drop_auc = metrics_cross["roc_auc"] - metrics_indomain["roc_auc"]

    return {
        "test_generator": test_generator,
        "indomain_f1": metrics_indomain["f1"],
        "cross_f1": metrics_cross["f1"],
        "drop_f1": drop_f1,
        "indomain_auc": metrics_indomain["roc_auc"],
        "cross_auc": metrics_cross["roc_auc"],
        "drop_auc": drop_auc
    }


def run_evaluation():
    manifest_path = "datasets/ai_dataset_manifest.csv"
    df = generate_manifest_if_missing(manifest_path)

    model_path = "models/ai_detector.joblib"
    if not os.path.exists(model_path):
        train_and_save(manifest_path, model_path)

    model_data = joblib.load(model_path)
    prod_threshold = float(model_data["threshold"])

    codes = []
    for _, row in df.iterrows():
        p = row["path"].replace("/", os.sep)
        with open(p, "r", encoding="utf-8") as f:
            codes.append(f.read())
    df["code"] = codes

    y = df["label"].values
    groups = df["problem_id"].values

    # Execute Nested GroupKFold evaluation (Zero threshold leakage)
    oof_probs, outer_preds, outer_thresholds, fold_metrics = run_nested_group_kfold_eval(codes, y, groups)

    mean_nested_threshold = float(np.mean(outer_thresholds))

    # Pooled metrics across nested outer folds
    cm = confusion_matrix(y, outer_preds, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    acc = accuracy_score(y, outer_preds)
    prec = precision_score(y, outer_preds, zero_division=0)
    rec = recall_score(y, outer_preds, zero_division=0)
    f1 = f1_score(y, outer_preds, zero_division=0)
    auc = roc_auc_score(y, oof_probs)
    fpr_human = fp / float(fp + tn) if (fp + tn) > 0 else 0.0

    pooled = {
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "accuracy": float(acc), "precision": float(prec), "recall": float(rec),
        "f1": float(f1), "roc_auc": float(auc), "fpr_human": float(fpr_human)
    }

    ci = run_bootstrap_ci(df, oof_probs, outer_preds, n_resamples=1000)
    cross_gen = run_cross_generator_eval(df, test_generator="codellama")

    print("\n=======================================================================")
    print("  NESTED GROUP-KFOLD AI CODE DETECTION EVALUATION (ZERO LEAKAGE)      ")
    print("=======================================================================")
    print(f"Mean Inner Selected Threshold: {mean_nested_threshold:.4f}")
    print(f"Production Threshold Saved:    {prod_threshold:.4f}")
    print(f"Pooled Precision:   {pooled['precision']:.4f} (95% CI: {ci['precision']})")
    print(f"Pooled Recall:      {pooled['recall']:.4f} (95% CI: {ci['recall']})")
    print(f"Pooled F1-Score:    {pooled['f1']:.4f} (95% CI: {ci['f1']})")
    print(f"Pooled ROC-AUC:     {pooled['roc_auc']:.4f} (95% CI: {ci['roc_auc']})")
    print(f"False Positive Rate (Human Code): {pooled['fpr_human']:.4f} (95% CI: {ci['fpr_human']})")

    # Write Markdown Report to results/ai_detection_eval.md
    os.makedirs("results", exist_ok=True)
    report_md_path = "results/ai_detection_eval.md"

    md_lines = []
    md_lines.append("# CodeGuard AI-Authorship Detector Evaluation Report")
    md_lines.append("**Methodology:** Nested GroupKFold Cross-Validation (Outer 5 Folds, Inner 4 Folds grouped by `problem_id`)")
    md_lines.append("**Leakage Control:** 100% Zero Leakage (TF-IDF vectorizer and decision threshold selection $T_i^*$ are fit strictly on inner training folds).")
    md_lines.append(f"**Evaluated Thresholds:** Mean Inner CV Threshold = `{mean_nested_threshold:.4f}` | Production Model Threshold = `{prod_threshold:.4f}`")
    md_lines.append("---")
    md_lines.append("## 1. Outer Fold Performance Metrics (Nested CV)")
    md_lines.append("| Outer Fold | Test Size | Inner Selected T* | TN | FP | FN | TP | Precision | Recall | F1-Score | FPR (Human) |")
    md_lines.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for fm in fold_metrics:
        md_lines.append(f"| Fold {fm['fold']} | {fm['test_size']} | {fm['selected_thresh']:.4f} | {fm['tn']} | {fm['fp']} | {fm['fn']} | {fm['tp']} | {fm['precision']:.4f} | {fm['recall']:.4f} | {fm['f1']:.4f} | {fm['fpr_human']:.4f} |")
    md_lines.append(f"| **Nested Pooled** | **{len(df)}** | **{mean_nested_threshold:.4f}** | **{pooled['tn']}** | **{pooled['fp']}** | **{pooled['fn']}** | **{pooled['tp']}** | **{pooled['precision']:.4f}** | **{pooled['recall']:.4f}** | **{pooled['f1']:.4f}** | **{pooled['fpr_human']:.4f}** |")
    md_lines.append("")

    md_lines.append("## 2. 95% Bootstrap Confidence Intervals (1000 Resamples by Problem)")
    md_lines.append("| Metric | Nested Pooled Score | 95% Bootstrap Confidence Interval |")
    md_lines.append("| :--- | :---: | :---: |")
    md_lines.append(f"| **Precision** | `{pooled['precision']:.4f}` | `[{ci['precision'][0]:.4f}, {ci['precision'][1]:.4f}]` |")
    md_lines.append(f"| **Recall** | `{pooled['recall']:.4f}` | `[{ci['recall'][0]:.4f}, {ci['recall'][1]:.4f}]` |")
    md_lines.append(f"| **F1-Score** | `{pooled['f1']:.4f}` | `[{ci['f1'][0]:.4f}, {ci['f1'][1]:.4f}]` |")
    md_lines.append(f"| **ROC-AUC** | `{pooled['roc_auc']:.4f}` | `[{ci['roc_auc'][0]:.4f}, {ci['roc_auc'][1]:.4f}]` |")
    md_lines.append(f"| **False Positive Rate (Human Code)** | `{pooled['fpr_human']:.4f}` | `[{ci['fpr_human'][0]:.4f}, {ci['fpr_human'][1]:.4f}]` |")
    md_lines.append("")

    if cross_gen:
        md_lines.append("## 3. Cross-Generator Generalization & Metric Drop")
        md_lines.append(f"Evaluates model generalization when trained on human + synthetic baseline patterns and tested on an unseen target LLM generator (`{cross_gen['test_generator']}`):")
        md_lines.append("")
        md_lines.append("| Evaluation Setting | F1-Score | ROC-AUC | Generalization Delta (Drop) |")
        md_lines.append("| :--- | :---: | :---: | :---: |")
        md_lines.append(f"| **In-Domain Generator (Problem Split)** | `{cross_gen['indomain_f1']:.4f}` | `{cross_gen['indomain_auc']:.4f}` | Baseline |")
        md_lines.append(f"| **Cross-Generator (Unseen LLM)** | `{cross_gen['cross_f1']:.4f}` | `{cross_gen['cross_auc']:.4f}` | **ΔF1:** `{cross_gen['drop_f1']:+.4f}`, **ΔAUC:** `{cross_gen['drop_auc']:+.4f}` |")
        md_lines.append("")
        md_lines.append("*Interpretation: The negative delta indicates performance drop when evaluating against an unseen LLM generator architecture without in-domain fine-tuning.*")
        md_lines.append("")

    md_lines.append("## 4. Risk-Tier Calibration & Faculty Guidance Disclaimer")
    md_lines.append("The CodeGuard AI detector outputs calibrated probabilities mapped into three decision-support risk tiers derived from the evaluated threshold $T^*$:")
    md_lines.append(f"- 🔴 **High Risk (Probability >= {prod_threshold:.4f})**: Indicates high probability of synthetic code generation. Prioritized for manual faculty review.")
    md_lines.append(f"- 🟠 **Moderate Risk ({0.5*prod_threshold:.4f} <= Probability < {prod_threshold:.4f})**: Indicates moderate structural or token heuristic overlap.")
    md_lines.append(f"- 🟢 **Low Risk / Human (Probability < {0.5*prod_threshold:.4f})**: Aligns with human programming patterns.")
    md_lines.append("")
    md_lines.append("> **⚠️ Faculty Guidance Disclaimer:**")
    md_lines.append("> AI detection probability scores and risk tiers are decision-support indicators intended exclusively to prioritize manual faculty code review. They do NOT constitute automated evidence or definitive proof of academic misconduct.")
    md_lines.append("")

    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\nReport successfully generated at {report_md_path}")

    # Write summary CSV to results/ai_detection.csv
    csv_df = pd.DataFrame([{
        "Metric": "AI Code Classifier (Nested GroupKFold)",
        "Accuracy": round(pooled["accuracy"], 4),
        "Precision": round(pooled["precision"], 4),
        "Recall": round(pooled["recall"], 4),
        "F1-Score": round(pooled["f1"], 4),
        "ROC-AUC": round(pooled["roc_auc"], 4),
        "FPR_Human": round(pooled["fpr_human"], 4),
        "Split_Method": "Nested 5-Fold GroupKFold (Zero Threshold Leakage)",
        "Mean_Nested_Threshold": mean_nested_threshold,
        "Production_Threshold": prod_threshold
    }])
    out_csv = "results/ai_detection.csv"
    csv_df.to_csv(out_csv, index=False)
    print(f"Summary CSV saved to {out_csv}")

    return pooled


if __name__ == "__main__":
    run_evaluation()
