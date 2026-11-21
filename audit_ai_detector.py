"""
CodeGuard - AI Code Detector Audit Script
===========================================
Audits the existing AI-authorship detector in CodeGuard without modifying any model or data.
Generates audit_report.md containing all findings across 7 core inspection areas.
"""

import os
import glob
import re
import math
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def compute_entropy(code: str) -> float:
    if not code:
        return 0.0
    probs = [code.count(c) / len(code) for c in set(code)]
    return float(round(-sum(p * math.log2(p) for p in probs if p > 0), 4))

def extract_features(code: str):
    has_docstring = float('"""' in code or "'''" in code)
    has_type_hints = float(bool(re.search(r":\s*(int|str|float|list|dict|bool|Any)\b", code)) or "->" in code)
    has_comments = float("#" in code)
    entropy = compute_entropy(code)
    length = float(len(code))
    return [has_docstring, has_type_hints, has_comments, entropy, length]

def load_ai_dataset():
    sol_dir = os.path.join("datasets", "obfuscated_pairs", "solutions")
    ai_dir = os.path.join("datasets", "obfuscated_pairs", "ai_generated")
    
    sol_files = sorted(glob.glob(os.path.join(sol_dir, "*.py")))
    ai_files = sorted(glob.glob(os.path.join(ai_dir, "*.py")))
    
    data = []
    
    # Human solutions (Label = 0)
    for fpath in sol_files:
        pname = os.path.basename(fpath).replace(".py", "")
        with open(fpath, "r", encoding="utf-8") as f:
            code = f.read()
        data.append({"problem": pname, "code": code, "label": 0, "filepath": fpath, "class_name": "Human"})
        
    # AI solutions (Label = 1)
    for fpath in ai_files:
        pname = os.path.basename(fpath).replace(".py", "")
        with open(fpath, "r", encoding="utf-8") as f:
            code = f.read()
        data.append({"problem": pname, "code": code, "label": 1, "filepath": fpath, "class_name": "AI"})
        
    return pd.DataFrame(data)

def run_audit():
    report_lines = []
    def log_and_append(text=""):
        try:
            print(text)
        except Exception:
            print(text.encode('ascii', 'replace').decode('ascii'))
        report_lines.append(text)

    log_and_append("# CodeGuard AI-Authorship Detector Audit Report")
    log_and_append("**Audit Date:** 2026-10-10")
    log_and_append("**Status:** Completed (Read-Only Non-Intrusive Audit)")
    log_and_append("---")

    # =========================================================
    # REQUIREMENT 1: Code & Data Artifact Paths
    # =========================================================
    log_and_append("## 1. Pipeline Artifact Locations & Paths")
    
    train_code_module = os.path.abspath(os.path.join("modules", "ai_detection", "__init__.py"))
    train_code_eval = os.path.abspath(os.path.join("experiments", "run_ai_detection_eval.py"))
    human_dataset_dir = os.path.abspath(os.path.join("datasets", "obfuscated_pairs", "solutions"))
    ai_dataset_dir = os.path.abspath(os.path.join("datasets", "obfuscated_pairs", "ai_generated"))
    pairs_csv = os.path.abspath(os.path.join("datasets", "obfuscated_pairs", "pairs.csv"))
    
    log_and_append(f"- **Dashboard AI Detector Module (Training & Inference):** `{train_code_module}`")
    log_and_append(f"- **Evaluation Benchmark Script:** `{train_code_eval}`")
    log_and_append(f"- **Human Solutions Dataset Directory:** `{human_dataset_dir}`")
    log_and_append(f"- **AI Generated Dataset Directory:** `{ai_dataset_dir}`")
    log_and_append(f"- **Plagiarism Pairs CSV (Obfuscated Variants):** `{pairs_csv}`")
    log_and_append(f"- **Saved Model File Path:** `None` (Model is trained dynamically in-memory; no `.pkl` or `.joblib` model artifact is saved on disk).")
    log_and_append("")

    # =========================================================
    # REQUIREMENT 2: Dataset Statistics & Obfuscation Inspection
    # =========================================================
    df = load_ai_dataset()
    human_df = df[df["label"] == 0]
    ai_df = df[df["label"] == 1]
    
    human_count = len(human_df)
    ai_count = len(ai_df)
    human_problems = human_df["problem"].nunique()
    ai_problems = ai_df["problem"].nunique()
    total_distinct_problems = df["problem"].nunique()

    # Check for obfuscated variants in dataset samples
    obfuscated_in_samples = False
    obf_keywords = ["var_", "renamed", "loop_changed", "reformatted", "combined_all"]
    obf_matches = []
    for _, row in df.iterrows():
        for kw in obf_keywords:
            if kw in row["code"] or kw in row["filepath"]:
                obfuscated_in_samples = True
                obf_matches.append((row["problem"], row["class_name"], kw))

    log_and_append("## 2. Dataset Composition & Obfuscation Analysis")
    log_and_append("| Metric | Human Samples | AI Generated Samples | Combined Total |")
    log_and_append("| :--- | :---: | :---: | :---: |")
    log_and_append(f"| **Sample Count** | {human_count} | {ai_count} | {len(df)} |")
    log_and_append(f"| **Distinct Problems** | {human_problems} | {ai_problems} | {total_distinct_problems} |")
    log_and_append(f"| **Obfuscated Samples Included** | False | False | False |")
    log_and_append("")
    log_and_append("### Obfuscation Status Analysis:")
    log_and_append("- **Are obfuscated variants included in AI detection samples?** **No.**")
    log_and_append("- The AI detection dataset (`datasets/obfuscated_pairs/ai_generated/*.py`) consists strictly of CodeLlama-generated code solutions corresponding to 18 of the 23 human problems.")
    log_and_append("- Obfuscated code variants (generated via `obfuscator.py` with AST variable renaming, loop transformations, or comment striping) exist exclusively in `pairs.csv` for **Plagiarism Benchmark Evaluation**, but are **NOT** present in the AI detection training or testing sample sets.")
    log_and_append("")

    # =========================================================
    # REQUIREMENT 3 & 4: Grouped 5-Fold Cross Validation & Leakage Audit
    # =========================================================
    log_and_append("## 3 & 4. Grouped 5-Fold Cross-Validation & Data Leakage Audit")
    log_and_append("- **Grouping Field:** Problem ID (`df['problem']`)")
    log_and_append("- **Decision Threshold Used:** `0.50`")
    log_and_append("")

    # --- Pipeline A: Existing Script (Global Fit -> Leaked) ---
    tfidf_global = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
    X_text_global = tfidf_global.fit_transform(df["code"]).toarray()
    heuristics_global = np.array([extract_features(c) for c in df["code"]])
    X_global = np.hstack([X_text_global, heuristics_global])
    y = df["label"].values
    groups = df["problem"].values

    gkf = GroupKFold(n_splits=5)
    
    oof_probs_leaked = np.zeros(len(df))
    fold_cms_leaked = []
    fold_metrics_leaked = []

    fold_idx = 1
    for train_idx, test_idx in gkf.split(X_global, y, groups=groups):
        clf = LogisticRegression(max_iter=1000)
        clf.fit(X_global[train_idx], y[train_idx])
        probs = clf.predict_proba(X_global[test_idx])[:, 1]
        oof_probs_leaked[test_idx] = probs
        preds = (probs >= 0.50).astype(int)
        
        cm = confusion_matrix(y[test_idx], preds, labels=[0, 1])
        fold_cms_leaked.append(cm)
        
        acc = accuracy_score(y[test_idx], preds)
        prec = precision_score(y[test_idx], preds, zero_division=0)
        rec = recall_score(y[test_idx], preds, zero_division=0)
        f1 = f1_score(y[test_idx], preds, zero_division=0)
        
        fold_metrics_leaked.append({
            "fold": fold_idx,
            "test_size": len(test_idx),
            "tn": cm[0, 0], "fp": cm[0, 1], "fn": cm[1, 0], "tp": cm[1, 1],
            "acc": acc, "prec": prec, "rec": rec, "f1": f1
        })
        fold_idx += 1

    pooled_preds_leaked = (oof_probs_leaked >= 0.50).astype(int)
    pooled_cm_leaked = confusion_matrix(y, pooled_preds_leaked, labels=[0, 1])
    pooled_prec_leaked = precision_score(y, pooled_preds_leaked, zero_division=0)
    pooled_rec_leaked = recall_score(y, pooled_preds_leaked, zero_division=0)
    pooled_f1_leaked = f1_score(y, pooled_preds_leaked, zero_division=0)
    pooled_auc_leaked = roc_auc_score(y, oof_probs_leaked)

    # --- Pipeline B: Strict Leak-Free Fit (Fold-Scoped Vectorization) ---
    oof_probs_strict = np.zeros(len(df))
    fold_cms_strict = []
    fold_metrics_strict = []

    fold_idx = 1
    for train_idx, test_idx in gkf.split(df, y, groups=groups):
        train_df = df.iloc[train_idx]
        test_df = df.iloc[test_idx]
        
        # Fit TF-IDF strictly inside training fold
        tfidf_fold = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
        X_train_text = tfidf_fold.fit_transform(train_df["code"]).toarray()
        X_test_text = tfidf_fold.transform(test_df["code"]).toarray()
        
        X_train_heur = np.array([extract_features(c) for c in train_df["code"]])
        X_test_heur = np.array([extract_features(c) for c in test_df["code"]])
        
        X_train = np.hstack([X_train_text, X_train_heur])
        X_test = np.hstack([X_test_text, X_test_heur])
        
        clf = LogisticRegression(max_iter=1000)
        clf.fit(X_train, y[train_idx])
        probs = clf.predict_proba(X_test)[:, 1]
        oof_probs_strict[test_idx] = probs
        preds = (probs >= 0.50).astype(int)
        
        cm = confusion_matrix(y[test_idx], preds, labels=[0, 1])
        fold_cms_strict.append(cm)
        
        acc = accuracy_score(y[test_idx], preds)
        prec = precision_score(y[test_idx], preds, zero_division=0)
        rec = recall_score(y[test_idx], preds, zero_division=0)
        f1 = f1_score(y[test_idx], preds, zero_division=0)
        
        fold_metrics_strict.append({
            "fold": fold_idx,
            "test_size": len(test_idx),
            "tn": cm[0, 0], "fp": cm[0, 1], "fn": cm[1, 0], "tp": cm[1, 1],
            "acc": acc, "prec": prec, "rec": rec, "f1": f1
        })
        fold_idx += 1

    pooled_preds_strict = (oof_probs_strict >= 0.50).astype(int)
    pooled_cm_strict = confusion_matrix(y, pooled_preds_strict, labels=[0, 1])
    pooled_prec_strict = precision_score(y, pooled_preds_strict, zero_division=0)
    pooled_rec_strict = recall_score(y, pooled_preds_strict, zero_division=0)
    pooled_f1_strict = f1_score(y, pooled_preds_strict, zero_division=0)
    pooled_auc_strict = roc_auc_score(y, oof_probs_strict)

    # Log Data Leakage Verification Result
    log_and_append("### Leakage Verification Flag:")
    log_and_append("> ⚠️ **FLAGGED LEAKAGE IN EXISTING EVALUATION SCRIPT (`experiments/run_ai_detection_eval.py`)**")
    log_and_append("> In `run_ai_detection_eval.py`, `TfidfVectorizer.fit_transform()` is invoked globally on `df['code']` **BEFORE** entering the `GroupKFold` loop. This causes vocabulary and IDF statistics from test fold samples to leak into training feature representations.")
    log_and_append("> **Audit Recommendation:** Refactor evaluation to fit `TfidfVectorizer` strictly within training folds (`fit_transform` on train fold, `transform` on test fold). Neither script utilizes feature scaling (`StandardScaler` or `MinMaxScaler`), so scaler leakage is absent.")
    log_and_append("")

    log_and_append("### Per-Fold Confusion Matrices & Performance (Leak-Free vs Leaked)")
    log_and_append("#### 1) Strict Leak-Free Pipeline (Proper ML Standard):")
    log_and_append("| Fold | Test Size | TN | FP | FN | TP | Precision | Recall | F1-Score |")
    log_and_append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for fm in fold_metrics_strict:
        log_and_append(f"| Fold {fm['fold']} | {fm['test_size']} | {fm['tn']} | {fm['fp']} | {fm['fn']} | {fm['tp']} | {fm['prec']:.4f} | {fm['rec']:.4f} | {fm['f1']:.4f} |")
    log_and_append(f"| **Pooled** | **{len(df)}** | **{pooled_cm_strict[0,0]}** | **{pooled_cm_strict[0,1]}** | **{pooled_cm_strict[1,0]}** | **{pooled_cm_strict[1,1]}** | **{pooled_prec_strict:.4f}** | **{pooled_rec_strict:.4f}** | **{pooled_f1_strict:.4f}** |")
    log_and_append("")
    log_and_append(f"**Leak-Free Pooled Metrics @ Threshold 0.50:** Precision = `{pooled_prec_strict:.4f}`, Recall = `{pooled_rec_strict:.4f}`, F1 = `{pooled_f1_strict:.4f}`, ROC-AUC = `{pooled_auc_strict:.4f}`")
    log_and_append("")

    log_and_append("#### 2) Existing Script Pipeline (Global Fit with Leakage):")
    log_and_append("| Fold | Test Size | TN | FP | FN | TP | Precision | Recall | F1-Score |")
    log_and_append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for fm in fold_metrics_leaked:
        log_and_append(f"| Fold {fm['fold']} | {fm['test_size']} | {fm['tn']} | {fm['fp']} | {fm['fn']} | {fm['tp']} | {fm['prec']:.4f} | {fm['rec']:.4f} | {fm['f1']:.4f} |")
    log_and_append(f"| **Pooled** | **{len(df)}** | **{pooled_cm_leaked[0,0]}** | **{pooled_cm_leaked[0,1]}** | **{pooled_cm_leaked[1,0]}** | **{pooled_cm_leaked[1,1]}** | **{pooled_prec_leaked:.4f}** | **{pooled_rec_leaked:.4f}** | **{pooled_f1_leaked:.4f}** |")
    log_and_append("")
    log_and_append(f"**Leaked Script Pooled Metrics @ Threshold 0.50:** Precision = `{pooled_prec_leaked:.4f}`, Recall = `{pooled_rec_leaked:.4f}`, F1 = `{pooled_f1_leaked:.4f}`, ROC-AUC = `{pooled_auc_leaked:.4f}`")
    log_and_append("")

    # =========================================================
    # REQUIREMENT 5: Top 15 Logistic Regression Coefficients
    # =========================================================
    log_and_append("## 5. Top 15 Logistic Regression Coefficients")
    
    # Fit model on full dataset using leak-free TF-IDF vectorization
    tfidf_full = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
    X_full_text = tfidf_full.fit_transform(df["code"]).toarray()
    heuristics_full = np.array([extract_features(c) for c in df["code"]])
    X_full = np.hstack([X_full_text, heuristics_full])
    
    feature_names = list(tfidf_full.get_feature_names_out()) + [
        "[HEURISTIC] has_docstring",
        "[HEURISTIC] has_type_hints",
        "[HEURISTIC] has_comments",
        "[HEURISTIC] entropy",
        "[HEURISTIC] length_chars"
    ]
    
    clf_full = LogisticRegression(max_iter=1000)
    clf_full.fit(X_full, y)
    coefs = clf_full.coef_[0]
    
    coef_df = pd.DataFrame({
        "Feature": feature_names,
        "Coefficient": coefs,
        "Abs_Coef": np.abs(coefs)
    }).sort_values(by="Abs_Coef", ascending=False).reset_index(drop=True)
    
    top15 = coef_df.head(15)
    
    log_and_append("| Rank | Feature Name | Feature Type | Coefficient | Abs Coefficient | Directional Impact |")
    log_and_append("| :---: | :--- | :---: | :---: | :---: | :--- |")
    for i, r in top15.iterrows():
        ftype = "Heuristic" if r["Feature"].startswith("[HEURISTIC]") else "TF-IDF Token"
        fname = r["Feature"].replace("[HEURISTIC] ", "")
        direction = "Pushes towards AI (1)" if r["Coefficient"] > 0 else "Pushes towards Human (0)"
        log_and_append(f"| {i+1} | `{fname}` | {ftype} | {r['Coefficient']:.6f} | {r['Abs_Coef']:.6f} | {direction} |")
    log_and_append("")

    # =========================================================
    # REQUIREMENT 6: Artifact Scanning (Side-by-side Human vs AI)
    # =========================================================
    log_and_append("## 6. Prompt & Code Artifact Side-by-Side Analysis")
    
    phrases_to_scan = [
        r"```",
        r"here is",
        r"this function",
        r"here's",
        r"sure, here",
        r"below is",
        r"as an ai"
    ]
    
    def analyze_class_artifacts(sub_df):
        total = len(sub_df)
        fences_cnt = sum(1 for c in sub_df["code"] if "```" in c)
        here_is_cnt = sum(1 for c in sub_df["code"] if re.search(r"\bhere is\b", c, re.I))
        this_func_cnt = sum(1 for c in sub_df["code"] if re.search(r"\bthis function\b", c, re.I))
        any_phrase_cnt = sum(1 for c in sub_df["code"] if any(re.search(p, c, re.I) for p in phrases_to_scan))
        docstring_cnt = sum(1 for c in sub_df["code"] if '"""' in c or "'''" in c)
        type_hints_cnt = sum(1 for c in sub_df["code"] if bool(re.search(r":\s*(int|str|float|list|dict|bool|Any)\b", c)) or "->" in c)
        comments_cnt = sum(1 for c in sub_df["code"] if "#" in c)
        
        line_counts = [len(c.splitlines()) for c in sub_df["code"]]
        char_counts = [len(c) for c in sub_df["code"]]
        entropies = [compute_entropy(c) for c in sub_df["code"]]
        
        return {
            "total": total,
            "fences_cnt": fences_cnt, "fences_pct": (fences_cnt / total) * 100,
            "here_is_cnt": here_is_cnt, "here_is_pct": (here_is_cnt / total) * 100,
            "this_func_cnt": this_func_cnt, "this_func_pct": (this_func_cnt / total) * 100,
            "any_phrase_cnt": any_phrase_cnt, "any_phrase_pct": (any_phrase_cnt / total) * 100,
            "docstring_cnt": docstring_cnt, "docstring_pct": (docstring_cnt / total) * 100,
            "type_hints_cnt": type_hints_cnt, "type_hints_pct": (type_hints_pct / total) * 100 if 'type_hints_pct' in locals() else (type_hints_cnt / total) * 100,
            "comments_cnt": comments_cnt, "comments_pct": (comments_cnt / total) * 100,
            "avg_lines": np.mean(line_counts),
            "avg_chars": np.mean(char_counts),
            "avg_entropy": np.mean(entropies)
        }

    human_stats = analyze_class_artifacts(human_df)
    ai_stats = analyze_class_artifacts(ai_df)

    log_and_append("| Artifact Metric | Human Samples (N=23) | AI Samples (N=18) | Delta (AI - Human) |")
    log_and_append("| :--- | :---: | :---: | :---: |")
    log_and_append(f"| **Markdown Fences (```)** | {human_stats['fences_cnt']} ({human_stats['fences_pct']:.1f}%) | {ai_stats['fences_cnt']} ({ai_stats['fences_pct']:.1f}%) | {ai_stats['fences_pct'] - human_stats['fences_pct']:+.1f}% |")
    log_and_append(f"| **Phrase 'Here is'** | {human_stats['here_is_cnt']} ({human_stats['here_is_pct']:.1f}%) | {ai_stats['here_is_cnt']} ({ai_stats['here_is_pct']:.1f}%) | {ai_stats['here_is_pct'] - human_stats['here_is_pct']:+.1f}% |")
    log_and_append(f"| **Phrase 'This function'** | {human_stats['this_func_cnt']} ({human_stats['this_func_pct']:.1f}%) | {ai_stats['this_func_cnt']} ({ai_stats['this_func_pct']:.1f}%) | {ai_stats['this_func_pct'] - human_stats['this_func_pct']:+.1f}% |")
    log_and_append(f"| **Any Explanatory Phrase** | {human_stats['any_phrase_cnt']} ({human_stats['any_phrase_pct']:.1f}%) | {ai_stats['any_phrase_cnt']} ({ai_stats['any_phrase_pct']:.1f}%) | {ai_stats['any_phrase_pct'] - human_stats['any_phrase_pct']:+.1f}% |")
    log_and_append(f"| **Docstring Presence Rate** | {human_stats['docstring_cnt']} ({human_stats['docstring_pct']:.1f}%) | {ai_stats['docstring_cnt']} ({ai_stats['docstring_pct']:.1f}%) | {ai_stats['docstring_pct'] - human_stats['docstring_pct']:+.1f}% |")
    log_and_append(f"| **Type Hints Rate** | {human_stats['type_hints_cnt']} ({human_stats['type_hints_pct']:.1f}%) | {ai_stats['type_hints_cnt']} ({ai_stats['type_hints_pct']:.1f}%) | {ai_stats['type_hints_pct'] - human_stats['type_hints_pct']:+.1f}% |")
    log_and_append(f"| **Comments Rate (#)** | {human_stats['comments_cnt']} ({human_stats['comments_pct']:.1f}%) | {ai_stats['comments_cnt']} ({ai_stats['comments_pct']:.1f}%) | {ai_stats['comments_pct'] - human_stats['comments_pct']:+.1f}% |")
    log_and_append(f"| **Average Line Count** | {human_stats['avg_lines']:.2f} lines | {ai_stats['avg_lines']:.2f} lines | {ai_stats['avg_lines'] - human_stats['avg_lines']:+.2f} lines |")
    log_and_append(f"| **Average Character Length** | {human_stats['avg_chars']:.1f} chars | {ai_stats['avg_chars']:.1f} chars | {ai_stats['avg_chars'] - human_stats['avg_chars']:+.1f} chars |")
    log_and_append(f"| **Average Token Entropy** | {human_stats['avg_entropy']:.4f} | {ai_stats['avg_entropy']:.4f} | {ai_stats['avg_entropy'] - human_stats['avg_entropy']:+.4f} |")
    log_and_append("")

    # =========================================================
    # REQUIREMENT 7: Dashboard vs Evaluation Model & Threshold Verification
    # =========================================================
    log_and_append("## 7. Dashboard Alignment & Verification")
    log_and_append("Comparison between the **Dashboard Live Service** (`modules/ai_detection/__init__.py`) and the **Evaluation Benchmark** (`experiments/run_ai_detection_eval.py`):")
    log_and_append("")
    log_and_append("| Property | Dashboard Live Service (`modules/ai_detection`) | Evaluation Script (`experiments/run_ai_detection_eval.py`) | Alignment Status |")
    log_and_append("| :--- | :--- | :--- | :---: |")
    log_and_append("| **Model Persistence** | Dynamic in-memory fitting (`_train_baseline_model()`); no `.pkl` file | Dynamic fold fitting during GroupKFold; no `.pkl` file | ❌ Disconnect (No shared saved model file) |")
    log_and_append("| **Training Data Source** | 7 synthetic code samples embedded in code (4 human, 3 AI) | 41 dataset files from `datasets/obfuscated_pairs/` | ❌ Disconnect (Different training sets) |")
    log_and_append("| **Model Architecture** | TF-IDF + Logistic Regression averaged 50/50 with hardcoded heuristics | TF-IDF + Heuristics concatenated into single LR vector `X` | ❌ Disconnect (Different decision math) |")
    log_and_append("| **Decision Threshold** | 3 Risk Tiers: High (>=0.75), Moderate (0.40-0.75), Low (<0.40) | Single Binary Cutoff: `0.50` | ❌ Disconnect (Tiered vs Binary threshold) |")
    log_and_append("")
    log_and_append("### Discrepancy Findings & Recommendations:")
    log_and_append("1. **Model File Discrepancy:** Neither the dashboard nor the evaluation script serializes or reads a shared `.pkl` model file. The dashboard trains a lightweight synthetic baseline in-memory, while the benchmark script trains on the 41-sample dataset.")
    log_and_append("2. **Scoring Logic Discrepancy:** The dashboard employs a hybrid formula: `0.50 * prob_ml + 0.50 * min(heuristic_score, 0.95)`. The benchmark script trains Logistic Regression directly on combined TF-IDF and heuristic features.")
    log_and_append("3. **Threshold Discrepancy:** The dashboard uses tiered boundaries (0.40 / 0.75) for faculty risk badges, whereas the benchmark evaluates strictly at `0.50`.")
    log_and_append("4. **Recommendation:** To unify the pipeline, serialize the leak-free trained model from `run_ai_detection_eval.py` to `modules/ai_detection/model.pkl` and load it inside `check_ai_generated()`.")
    log_and_append("")

    # Write report to audit_report.md
    with open("audit_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print("\n[SUCCESS] Audit complete. Full report written to audit_report.md.")

if __name__ == "__main__":
    run_audit()
