# CodeGuard AI-Authorship Detector Audit Report
**Audit Date:** 2026-10-10
**Status:** Completed (Read-Only Non-Intrusive Audit)
---
## 1. Pipeline Artifact Locations & Paths
- **Dashboard AI Detector Module (Training & Inference):** `C:\Users\mbgra\Desktop\codeguard\modules\ai_detection\__init__.py`
- **Evaluation Benchmark Script:** `C:\Users\mbgra\Desktop\codeguard\experiments\run_ai_detection_eval.py`
- **Human Solutions Dataset Directory:** `C:\Users\mbgra\Desktop\codeguard\datasets\obfuscated_pairs\solutions`
- **AI Generated Dataset Directory:** `C:\Users\mbgra\Desktop\codeguard\datasets\obfuscated_pairs\ai_generated`
- **Plagiarism Pairs CSV (Obfuscated Variants):** `C:\Users\mbgra\Desktop\codeguard\datasets\obfuscated_pairs\pairs.csv`
- **Saved Model File Path:** `None` (Model is trained dynamically in-memory; no `.pkl` or `.joblib` model artifact is saved on disk).

## 2. Dataset Composition & Obfuscation Analysis
| Metric | Human Samples | AI Generated Samples | Combined Total |
| :--- | :---: | :---: | :---: |
| **Sample Count** | 23 | 18 | 41 |
| **Distinct Problems** | 23 | 18 | 23 |
| **Obfuscated Samples Included** | False | False | False |

### Obfuscation Status Analysis:
- **Are obfuscated variants included in AI detection samples?** **No.**
- The AI detection dataset (`datasets/obfuscated_pairs/ai_generated/*.py`) consists strictly of CodeLlama-generated code solutions corresponding to 18 of the 23 human problems.
- Obfuscated code variants (generated via `obfuscator.py` with AST variable renaming, loop transformations, or comment striping) exist exclusively in `pairs.csv` for **Plagiarism Benchmark Evaluation**, but are **NOT** present in the AI detection training or testing sample sets.

## 3 & 4. Grouped 5-Fold Cross-Validation & Data Leakage Audit
- **Grouping Field:** Problem ID (`df['problem']`)
- **Decision Threshold Used:** `0.50`

### Leakage Verification Flag:
> ⚠️ **FLAGGED LEAKAGE IN EXISTING EVALUATION SCRIPT (`experiments/run_ai_detection_eval.py`)**
> In `run_ai_detection_eval.py`, `TfidfVectorizer.fit_transform()` is invoked globally on `df['code']` **BEFORE** entering the `GroupKFold` loop. This causes vocabulary and IDF statistics from test fold samples to leak into training feature representations.
> **Audit Recommendation:** Refactor evaluation to fit `TfidfVectorizer` strictly within training folds (`fit_transform` on train fold, `transform` on test fold). Neither script utilizes feature scaling (`StandardScaler` or `MinMaxScaler`), so scaler leakage is absent.

### Per-Fold Confusion Matrices & Performance (Leak-Free vs Leaked)
#### 1) Strict Leak-Free Pipeline (Proper ML Standard):
| Fold | Test Size | TN | FP | FN | TP | Precision | Recall | F1-Score |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 9 | 5 | 0 | 2 | 2 | 1.0000 | 0.5000 | 0.6667 |
| Fold 2 | 8 | 4 | 0 | 4 | 0 | 0.0000 | 0.0000 | 0.0000 |
| Fold 3 | 8 | 3 | 1 | 2 | 2 | 0.6667 | 0.5000 | 0.5714 |
| Fold 4 | 8 | 3 | 2 | 1 | 2 | 0.5000 | 0.6667 | 0.5714 |
| Fold 5 | 8 | 5 | 0 | 3 | 0 | 0.0000 | 0.0000 | 0.0000 |
| **Pooled** | **41** | **20** | **3** | **12** | **6** | **0.6667** | **0.3333** | **0.4444** |

**Leak-Free Pooled Metrics @ Threshold 0.50:** Precision = `0.6667`, Recall = `0.3333`, F1 = `0.4444`, ROC-AUC = `0.6691`

#### 2) Existing Script Pipeline (Global Fit with Leakage):
| Fold | Test Size | TN | FP | FN | TP | Precision | Recall | F1-Score |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 9 | 5 | 0 | 3 | 1 | 1.0000 | 0.2500 | 0.4000 |
| Fold 2 | 8 | 4 | 0 | 4 | 0 | 0.0000 | 0.0000 | 0.0000 |
| Fold 3 | 8 | 3 | 1 | 2 | 2 | 0.6667 | 0.5000 | 0.5714 |
| Fold 4 | 8 | 3 | 2 | 1 | 2 | 0.5000 | 0.6667 | 0.5714 |
| Fold 5 | 8 | 5 | 0 | 3 | 0 | 0.0000 | 0.0000 | 0.0000 |
| **Pooled** | **41** | **20** | **3** | **13** | **5** | **0.6250** | **0.2778** | **0.3846** |

**Leaked Script Pooled Metrics @ Threshold 0.50:** Precision = `0.6250`, Recall = `0.2778`, F1 = `0.3846`, ROC-AUC = `0.6498`

## 5. Top 15 Logistic Regression Coefficients
| Rank | Feature Name | Feature Type | Coefficient | Abs Coefficient | Directional Impact |
| :---: | :--- | :---: | :---: | :---: | :--- |
| 1 | `entropy` | Heuristic | 0.769273 | 0.769273 | Pushes towards AI (1) |
| 2 | `result` | TF-IDF Token | -0.629360 | 0.629360 | Pushes towards Human (0) |
| 3 | `total` | TF-IDF Token | -0.617200 | 0.617200 | Pushes towards Human (0) |
| 4 | `has_comments` | Heuristic | 0.604429 | 0.604429 | Pushes towards AI (1) |
| 5 | `num` | TF-IDF Token | -0.448248 | 0.448248 | Pushes towards Human (0) |
| 6 | `flattened` | TF-IDF Token | 0.376920 | 0.376920 | Pushes towards AI (1) |
| 7 | `words` | TF-IDF Token | -0.323941 | 0.323941 | Pushes towards Human (0) |
| 8 | `ch` | TF-IDF Token | -0.294913 | 0.294913 | Pushes towards Human (0) |
| 9 | `seen` | TF-IDF Token | -0.272545 | 0.272545 | Pushes towards Human (0) |
| 10 | `the` | TF-IDF Token | 0.254469 | 0.254469 | Pushes towards AI (1) |
| 11 | `return` | TF-IDF Token | 0.245047 | 0.245047 | Pushes towards AI (1) |
| 12 | `else` | TF-IDF Token | 0.241266 | 0.241266 | Pushes towards AI (1) |
| 13 | `flat` | TF-IDF Token | -0.234288 | 0.234288 | Pushes towards Human (0) |
| 14 | `char` | TF-IDF Token | 0.227085 | 0.227085 | Pushes towards AI (1) |
| 15 | `lower` | TF-IDF Token | -0.217012 | 0.217012 | Pushes towards Human (0) |

## 6. Prompt & Code Artifact Side-by-Side Analysis
| Artifact Metric | Human Samples (N=23) | AI Samples (N=18) | Delta (AI - Human) |
| :--- | :---: | :---: | :---: |
| **Markdown Fences (```)** | 0 (0.0%) | 0 (0.0%) | +0.0% |
| **Phrase 'Here is'** | 0 (0.0%) | 0 (0.0%) | +0.0% |
| **Phrase 'This function'** | 0 (0.0%) | 0 (0.0%) | +0.0% |
| **Any Explanatory Phrase** | 0 (0.0%) | 0 (0.0%) | +0.0% |
| **Docstring Presence Rate** | 0 (0.0%) | 0 (0.0%) | +0.0% |
| **Type Hints Rate** | 0 (0.0%) | 0 (0.0%) | +0.0% |
| **Comments Rate (#)** | 0 (0.0%) | 2 (11.1%) | +11.1% |
| **Average Line Count** | 7.04 lines | 5.89 lines | -1.15 lines |
| **Average Character Length** | 166.4 chars | 145.5 chars | -20.9 chars |
| **Average Token Entropy** | 3.7932 | 3.9157 | +0.1225 |

## 7. Dashboard Alignment & Verification
Comparison between the **Dashboard Live Service** (`modules/ai_detection/__init__.py`) and the **Evaluation Benchmark** (`experiments/run_ai_detection_eval.py`):

| Property | Dashboard Live Service (`modules/ai_detection`) | Evaluation Script (`experiments/run_ai_detection_eval.py`) | Alignment Status |
| :--- | :--- | :--- | :---: |
| **Model Persistence** | Dynamic in-memory fitting (`_train_baseline_model()`); no `.pkl` file | Dynamic fold fitting during GroupKFold; no `.pkl` file | ❌ Disconnect (No shared saved model file) |
| **Training Data Source** | 7 synthetic code samples embedded in code (4 human, 3 AI) | 41 dataset files from `datasets/obfuscated_pairs/` | ❌ Disconnect (Different training sets) |
| **Model Architecture** | TF-IDF + Logistic Regression averaged 50/50 with hardcoded heuristics | TF-IDF + Heuristics concatenated into single LR vector `X` | ❌ Disconnect (Different decision math) |
| **Decision Threshold** | 3 Risk Tiers: High (>=0.75), Moderate (0.40-0.75), Low (<0.40) | Single Binary Cutoff: `0.50` | ❌ Disconnect (Tiered vs Binary threshold) |

### Discrepancy Findings & Recommendations:
1. **Model File Discrepancy:** Neither the dashboard nor the evaluation script serializes or reads a shared `.pkl` model file. The dashboard trains a lightweight synthetic baseline in-memory, while the benchmark script trains on the 41-sample dataset.
2. **Scoring Logic Discrepancy:** The dashboard employs a hybrid formula: `0.50 * prob_ml + 0.50 * min(heuristic_score, 0.95)`. The benchmark script trains Logistic Regression directly on combined TF-IDF and heuristic features.
3. **Threshold Discrepancy:** The dashboard uses tiered boundaries (0.40 / 0.75) for faculty risk badges, whereas the benchmark evaluates strictly at `0.50`.
4. **Recommendation:** To unify the pipeline, serialize the leak-free trained model from `run_ai_detection_eval.py` to `modules/ai_detection/model.pkl` and load it inside `check_ai_generated()`.
