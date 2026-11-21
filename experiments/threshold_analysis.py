"""
Threshold Analysis — CodeGuard AI-Authorship Detector
=====================================================
Produces a threshold-versus-metrics table from nested GroupKFold
out-of-fold predictions.  Evaluates thresholds 0.30–0.70 in steps
of 0.01, with explicit rows for the current production threshold
(0.39) and the two suggested candidates (0.55, 0.60).

Selection objective is documented inline and written to the report.

Output: results/threshold_analysis.md
"""

import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sklearn.model_selection import GroupKFold
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)
from modules.ai_detection.model import build_pipeline
from experiments.train_ai_detector import generate_manifest_if_missing


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def select_best_threshold(y_true, y_probs):
    best_t, best_f1 = 0.50, -1.0
    for t in np.linspace(0.10, 0.90, 81):
        f1 = f1_score(y_true, (y_probs >= t).astype(int), zero_division=0)
        if f1 > best_f1:
            best_f1, best_t = f1, float(round(t, 4))
    return best_t


def nested_cv_oof(codes, y, groups):
    """Return out-of-fold probabilities from nested GroupKFold."""
    outer_gkf = GroupKFold(n_splits=5)
    oof = np.zeros(len(codes))

    for tr_idx, te_idx in outer_gkf.split(codes, y, groups=groups):
        tr_c = [codes[i] for i in tr_idx]
        tr_y, tr_g = y[tr_idx], groups[tr_idx]
        te_c = [codes[i] for i in te_idx]

        # Inner CV for threshold (not used here — we sweep externally)
        pipe = build_pipeline()
        pipe.fit(tr_c, tr_y)
        oof[te_idx] = pipe.predict_proba(te_c)[:, 1]

    return oof


def metrics_at_threshold(y, probs, t):
    preds = (probs >= t).astype(int)
    cm = confusion_matrix(y, preds, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    prec = precision_score(y, preds, zero_division=0)
    rec = recall_score(y, preds, zero_division=0)
    f1 = f1_score(y, preds, zero_division=0)
    return dict(threshold=t, tn=tn, fp=fp, fn=fn, tp=tp,
                fpr=fpr, precision=prec, recall=rec, f1=f1)


# ──────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────

def run_threshold_analysis():
    lines = []
    def log(t=""):
        print(t.encode("ascii", errors="replace").decode("ascii"))
        lines.append(t)

    # Load data
    df = generate_manifest_if_missing("datasets/ai_dataset_manifest.csv")
    codes = []
    for _, row in df.iterrows():
        p = row["path"].replace("/", os.sep)
        with open(p, encoding="utf-8") as f:
            codes.append(f.read())
    y = df["label"].values
    groups = df["problem_id"].values

    # Generate OOF predictions via nested CV
    log("Generating out-of-fold predictions (5-fold GroupKFold, outer only)...")
    oof = nested_cv_oof(codes, y, groups)
    roc_auc = roc_auc_score(y, oof)
    log(f"Pooled ROC-AUC from OOF probabilities: {roc_auc:.4f}")
    log("")

    # ── Threshold sweep ────────────────────────────────────
    thresholds = sorted(set(
        list(np.round(np.arange(0.30, 0.71, 0.01), 2)) +
        [0.39, 0.55, 0.60]  # explicit candidates
    ))

    rows = []
    for t in thresholds:
        rows.append(metrics_at_threshold(y, oof, t))
    sweep_df = pd.DataFrame(rows)

    # ── Table output ───────────────────────────────────────
    log("# Threshold Analysis — AI-Authorship Detector")
    log("")
    log(f"**Dataset:** {len(df)} samples, {df['problem_id'].nunique()} independent problems, "
        f"{sum(y)} AI / {sum(y==0)} Human")
    log(f"**Method:** Out-of-fold probabilities from 5-fold GroupKFold (grouped by `problem_id`)")
    log(f"**ROC-AUC (pooled):** `{roc_auc:.4f}`")
    log("")
    log("## Full Sweep: Threshold vs. Metrics")
    log("")
    log("| Threshold | FPR (Human) | Recall (AI) | Precision | F1 | TP | FP | FN | TN | Note |")
    log("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")

    highlight = {0.39: "Current production", 0.55: "Candidate A", 0.60: "Candidate B"}
    for _, r in sweep_df.iterrows():
        t = r["threshold"]
        note = highlight.get(t, "")
        marker = " **" if t in highlight else ""
        end = "**" if t in highlight else ""
        log(f"| {marker}{t:.2f}{end} | {r['fpr']:.3f} | {r['recall']:.3f} | "
            f"{r['precision']:.3f} | {r['f1']:.3f} | {int(r['tp'])} | {int(r['fp'])} | "
            f"{int(r['fn'])} | {int(r['tn'])} | {note} |")

    log("")

    # ── Focused comparison ─────────────────────────────────
    log("## Focused Comparison: Current vs. Candidates")
    log("")
    log("| | T = 0.39 (current) | T = 0.55 | T = 0.60 |")
    log("| :--- | :---: | :---: | :---: |")
    for metric_name in ["fpr", "recall", "precision", "f1"]:
        vals = []
        for t in [0.39, 0.55, 0.60]:
            row = sweep_df[sweep_df["threshold"] == t].iloc[0]
            vals.append(f"`{row[metric_name]:.3f}`")
        label = {"fpr": "FPR (Human flagged)", "recall": "Recall (AI caught)",
                 "precision": "Precision", "f1": "F1"}[metric_name]
        log(f"| **{label}** | {' | '.join(vals)} |")
    log("")

    # ── Threshold selection with documented objective ──────
    log("## Threshold Selection Objective")
    log("")
    log("**Constraint:** FPR on human code must be <= 0.25 (at most 1 in 4 genuine ")
    log("human submissions flagged for review).")
    log("")
    log("**Objective:** Among thresholds satisfying the FPR constraint, select the one ")
    log("that maximises F1 to balance recall and precision.")
    log("")

    feasible = sweep_df[sweep_df["fpr"] <= 0.25].copy()
    if len(feasible) == 0:
        log("> **No threshold in [0.30, 0.70] achieves FPR ≤ 0.25.** "
            "The model cannot reliably separate human from AI code at any "
            "operating point within this range.")
        log("")
        # Fall back: pick the threshold with lowest FPR that still has recall > 0
        fallback = sweep_df[sweep_df["recall"] > 0].sort_values("fpr").iloc[0]
        selected_t = float(fallback["threshold"])
        log(f"**Fallback:** Selecting T = `{selected_t:.2f}` (lowest FPR with non-zero recall).")
        log(f"FPR = `{fallback['fpr']:.3f}`, Recall = `{fallback['recall']:.3f}`, "
            f"F1 = `{fallback['f1']:.3f}`")
    else:
        best_row = feasible.sort_values("f1", ascending=False).iloc[0]
        selected_t = float(best_row["threshold"])
        log(f"**Selected threshold:** `{selected_t:.2f}`")
        log(f"- FPR = `{best_row['fpr']:.3f}` (within <= 0.25 constraint)")
        log(f"- Recall = `{best_row['recall']:.3f}`")
        log(f"- Precision = `{best_row['precision']:.3f}`")
        log(f"- F1 = `{best_row['f1']:.3f}`")
    log("")

    # ── Inconclusive tier definition ───────────────────────
    log("## Proposed Review Tiers (Three-Tier Policy)")
    log("")
    low_t = selected_t * 0.5
    log(f"| Tier | Score Range | Dashboard Label | Action |")
    log(f"| :--- | :---: | :--- | :--- |")
    log(f"| **Flagged** | `>= {selected_t:.2f}` | [!] Flagged for Review | Faculty should review for AI markers |")
    log(f"| **Inconclusive** | `[{low_t:.2f}, {selected_t:.2f})` | [?] Inconclusive | Insufficient evidence to flag or clear |")
    log(f"| **Routine** | `< {low_t:.2f}` | [OK] Routine Code | No action needed |")
    log("")
    log("> The inconclusive tier explicitly communicates that the model cannot ")
    log("> confidently classify the submission. This prevents both false accusations ")
    log("> and false assurances.")
    log("")

    # ── Generator-specific threshold behaviour ─────────────
    log("## Generator-Specific Behaviour at Selected Threshold")
    log("")
    for gen in df[df["label"] == 1]["generator"].unique():
        gen_mask = (df["generator"].values == gen) & (df["label"].values == 1)
        gen_probs = oof[gen_mask]
        caught = int(np.sum(gen_probs >= selected_t))
        total = int(np.sum(gen_mask))
        log(f"- **{gen}**: {caught}/{total} caught (recall = {caught/total:.2f})")
    human_mask = df["label"].values == 0
    human_flagged = int(np.sum(oof[human_mask] >= selected_t))
    human_total = int(np.sum(human_mask))
    log(f"- **Human**: {human_flagged}/{human_total} false positives "
        f"(FPR = {human_flagged/human_total:.2f})")
    log("")

    # ── Save ───────────────────────────────────────────────
    os.makedirs("results", exist_ok=True)
    with open("results/threshold_analysis.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\nSaved to results/threshold_analysis.md")

    return selected_t


if __name__ == "__main__":
    run_threshold_analysis()
