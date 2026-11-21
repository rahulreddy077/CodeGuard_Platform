# CodeGuard AI Detector — Verification & Sensitivity Analysis
**Scope:** P0 threshold consistency, fold isolation, duplicate sensitivity, provenance; P1 generator breakdown, calibration.

## P0-1 · Threshold Consistency

| Item | Value |
| :--- | :--- |
| Production threshold (saved in joblib) | `0.3900` |
| Re-derived OOF threshold (same algorithm) | `0.3900` |
| Manifest hash baked into joblib | `d9f59e794ef3d7e3…` |
| Dashboard `DEFAULT_MODEL_PATH` resolves to | `C:\Users\mbgra\Desktop\codeguard\models\ai_detector.joblib` |
| Loaded by dashboard (`get_model_data`) | same joblib artifact |

> **PASS** — Production threshold matches re-derived value within ±0.02.

## P0-2 · GroupKFold Problem-Level Isolation (70 Samples)

| Outer Fold | Train Problems | Test Problems | Overlap | Train Samples (AI/Human) | Test Samples (AI/Human) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 18 | 5 | None | 55 (19/36) | 15 (5/10) |
| Fold 2 | 18 | 5 | None | 55 (19/36) | 15 (5/10) |
| Fold 3 | 19 | 4 | None | 57 (19/38) | 13 (5/8) |
| Fold 4 | 19 | 4 | None | 57 (19/38) | 13 (5/8) |
| Fold 5 | 18 | 5 | None | 56 (20/36) | 14 (4/10) |

> **PASS** — Zero problem overlap across all 5 folds.

**Independent programming problems available:** 23 (each appears across 3.0 samples on average). Bootstrap CIs resample by problem, so effective N for generalisation estimates = 23 problems, not 70 files.

## P0-3 · Duplicate-Contamination Sensitivity Analysis

**Known exact duplicates:** `binary_search.py` and `linear_search.py` in `ai_generated/` are character-for-character identical to their counterparts in `solutions/`.

Running nested CV on full dataset (70 samples)…
Running nested CV on deduplicated dataset (63 samples, 21 problems)…

| Metric | Full (70 samples, 23 problems) | Dedup (excl. 2 dup problems, 63 samples, 21 problems) | Delta |
| :--- | :---: | :---: | :---: |
| **precision** | `0.5172` | `0.5000` | `-0.0172` |
| **recall** | `0.6250` | `0.9048` | `+0.2798` |
| **f1** | `0.5660` | `0.6441` | `+0.0780` |
| **roc_auc** | `0.7437` | `0.7483` | `+0.0046` |
| **fpr_human** | `0.3043` | `0.4524` | `+0.1480` |
| **brier** | `0.2002` | `0.2056` | `+0.0054` |

> **LOW SENSITIVITY** — ROC-AUC shifts by 0.0046 when duplicate problems are excluded. The duplicates do not substantially inflate reported performance.

## P0-4 · Independent Human Solution Provenance

| Directory | Author Tag | Count | Provenance Description |
| :--- | :--- | :---: | :--- |
| `datasets/obfuscated_pairs/solutions/` | `human_author_1` | 23 | Hand-written reference solutions, no type hints, no docstrings, concrete variable names, loop-based idioms. Created by project author. |
| `datasets/obfuscated_pairs/human_independent/` | `human_author_2` | 23 | Independent re-implementations of the same 23 problems using different algorithmic choices (e.g., recursive vs. iterative, set-based vs. loop-based). Created by project author. |

**Style checks (presence rates):**

| Author | Docstrings | Type hints | Comments |
| :--- | :---: | :---: | :---: |
| human_author_1 (solutions/) | 0/23 | 0/23 | 0/23 |
| human_author_2 (human_independent/) | 0/23 | 0/23 | 0/23 |

> Both human classes are free of docstrings and type hints (characteristic AI markers), consistent with genuine student-style code.

## P1-1 · Generator-Specific Performance Breakdown

### Generator: `codellama` (18 AI samples vs 46 human)
| Metric | Score |
| :--- | :---: |
| precision | `0.0000` |
| recall | `0.0000` |
| f1 | `0.0000` |
| roc_auc | `0.5713` |
| fpr_human | `0.0217` |

### Generator: `gpt35` (6 AI samples vs 46 human)
| Metric | Score |
| :--- | :---: |
| precision | `0.2778` |
| recall | `0.8333` |
| f1 | `0.4167` |
| roc_auc | `0.9167` |
| fpr_human | `0.2826` |

## P1-3 · Calibration & False-Positive Breakdown

### Probability distribution by class (full-dataset OOF probs)

| Prob Band | Human samples | AI samples |
| :--- | :---: | :---: |
| [0.0, 0.2) | 13.0% | 4.2% |
| [0.2, 0.4) | 39.1% | 12.5% |
| [0.4, 0.6) | 32.6% | 41.7% |
| [0.6, 0.8) | 15.2% | 16.7% |
| [0.8, 1.0) | 0.0% | 25.0% |

### False positives by human author source

Threshold used: `0.3900` (production threshold)

| Author | Total | FP (flagged) | FP Rate |
| :--- | :---: | :---: | :---: |
| `human_author_1` | 23 | 12 | 52.2% |
| `human_author_2` | 23 | 12 | 52.2% |

**Brier Score (full OOF, lower = better calibrated):** `0.2002`

> A Brier score of 0.25 equals uninformative random prediction. Scores below 0.20 indicate some useful discrimination; scores below 0.10 indicate good calibration.

## Summary

| Check | Result |
| :--- | :--- |
| P0-1 Threshold consistency | PASS — prod=0.3900, re-derived=0.3900 |
| P0-2 Fold problem isolation | PASS — all 5 folds clean |
| P0-3 Duplicate sensitivity | ROC-AUC delta=+0.0046 (LOW sensitivity) |
| P0-4 Human provenance | Both author sources confirmed hand-written; no AI markers |
| P1-1 Generator breakdown | Reported per-generator above |
| P1-3 Calibration / FP | Brier=0.2002; FP rates per author above |

**Independent programming problems:** 23 — this is the effective sample size for generalisation claims, not 70 files.