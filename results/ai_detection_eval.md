# CodeGuard AI-Authorship Detector Evaluation Report
**Methodology:** Nested GroupKFold Cross-Validation (Outer 5 Folds, Inner 4 Folds grouped by `problem_id`)
**Leakage Control:** 100% Zero Leakage (TF-IDF vectorizer and decision threshold selection $T_i^*$ are fit strictly on inner training folds).
**Evaluated Thresholds:** Mean Inner CV Threshold = `0.5060` | Production Model Threshold = `0.5400`
---
## 1. Outer Fold Performance Metrics (Nested CV)
| Outer Fold | Test Size | Inner Selected T* | TN | FP | FN | TP | Precision | Recall | F1-Score | FPR (Human) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 15 | 0.4400 | 8 | 2 | 2 | 3 | 0.6000 | 0.6000 | 0.6000 | 0.2000 |
| Fold 2 | 15 | 0.5200 | 7 | 3 | 2 | 3 | 0.5000 | 0.6000 | 0.5455 | 0.3000 |
| Fold 3 | 13 | 0.5400 | 5 | 3 | 2 | 3 | 0.5000 | 0.6000 | 0.5455 | 0.3750 |
| Fold 4 | 13 | 0.4300 | 4 | 4 | 0 | 5 | 0.5556 | 1.0000 | 0.7143 | 0.5000 |
| Fold 5 | 14 | 0.6000 | 8 | 2 | 2 | 2 | 0.5000 | 0.5000 | 0.5000 | 0.2000 |
| **Nested Pooled** | **70** | **0.5060** | **32** | **14** | **8** | **16** | **0.5333** | **0.6667** | **0.5926** | **0.3043** |

## 2. 95% Bootstrap Confidence Intervals (1000 Resamples by Problem)
| Metric | Nested Pooled Score | 95% Bootstrap Confidence Interval |
| :--- | :---: | :---: |
| **Precision** | `0.5333` | `[0.4231, 0.6800]` |
| **Recall** | `0.6667` | `[0.4800, 0.8335]` |
| **F1-Score** | `0.5926` | `[0.4681, 0.6984]` |
| **ROC-AUC** | `0.7437` | `[0.6408, 0.8392]` |
| **False Positive Rate (Human Code)** | `0.3043` | `[0.1522, 0.4565]` |

## 3. Cross-Generator Generalization & Metric Drop
Evaluates model generalization when trained on human + synthetic baseline patterns and tested on an unseen target LLM generator (`codellama`):

| Evaluation Setting | F1-Score | ROC-AUC | Generalization Delta (Drop) |
| :--- | :---: | :---: | :---: |
| **In-Domain Generator (Problem Split)** | `0.7000` | `0.8333` | Baseline |
| **Cross-Generator (Unseen LLM)** | `0.5000` | `0.5833` | **ΔF1:** `-0.2000`, **ΔAUC:** `-0.2500` |

*Interpretation: The negative delta indicates performance drop when evaluating against an unseen LLM generator architecture without in-domain fine-tuning.*

## 4. Risk-Tier Calibration & Faculty Guidance Disclaimer
The CodeGuard AI detector outputs calibrated probabilities mapped into three decision-support risk tiers derived from the evaluated threshold $T^*$:
- 🔴 **High Risk (Probability >= 0.5400)**: Indicates high probability of synthetic code generation. Prioritized for manual faculty review.
- 🟠 **Moderate Risk (0.2700 <= Probability < 0.5400)**: Indicates moderate structural or token heuristic overlap.
- 🟢 **Low Risk / Human (Probability < 0.2700)**: Aligns with human programming patterns.

> **⚠️ Faculty Guidance Disclaimer:**
> AI detection probability scores and risk tiers are decision-support indicators intended exclusively to prioritize manual faculty code review. They do NOT constitute automated evidence or definitive proof of academic misconduct.
