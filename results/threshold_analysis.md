Generating out-of-fold predictions (5-fold GroupKFold, outer only)...
Pooled ROC-AUC from OOF probabilities: 0.7437

# Threshold Analysis — AI-Authorship Detector

**Dataset:** 70 samples, 23 independent problems, 24 AI / 46 Human
**Method:** Out-of-fold probabilities from 5-fold GroupKFold (grouped by `problem_id`)
**ROC-AUC (pooled):** `0.7437`

## Full Sweep: Threshold vs. Metrics

| Threshold | FPR (Human) | Recall (AI) | Precision | F1 | TP | FP | FN | TN | Note |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 0.30 | 0.674 | 0.958 | 0.426 | 0.590 | 23 | 31 | 1 | 15 |  |
| 0.31 | 0.652 | 0.917 | 0.423 | 0.579 | 22 | 30 | 2 | 16 |  |
| 0.32 | 0.652 | 0.917 | 0.423 | 0.579 | 22 | 30 | 2 | 16 |  |
| 0.33 | 0.609 | 0.917 | 0.440 | 0.595 | 22 | 28 | 2 | 18 |  |
| 0.34 | 0.609 | 0.875 | 0.429 | 0.575 | 21 | 28 | 3 | 18 |  |
| 0.35 | 0.609 | 0.875 | 0.429 | 0.575 | 21 | 28 | 3 | 18 |  |
| 0.36 | 0.609 | 0.875 | 0.429 | 0.575 | 21 | 28 | 3 | 18 |  |
| 0.37 | 0.587 | 0.875 | 0.438 | 0.583 | 21 | 27 | 3 | 19 |  |
| 0.38 | 0.543 | 0.875 | 0.457 | 0.600 | 21 | 25 | 3 | 21 |  |
|  **0.39** | 0.522 | 0.875 | 0.467 | 0.609 | 21 | 24 | 3 | 22 | Current production |
| 0.40 | 0.478 | 0.833 | 0.476 | 0.606 | 20 | 22 | 4 | 24 |  |
| 0.41 | 0.478 | 0.792 | 0.463 | 0.585 | 19 | 22 | 5 | 24 |  |
| 0.42 | 0.435 | 0.792 | 0.487 | 0.603 | 19 | 20 | 5 | 26 |  |
| 0.43 | 0.435 | 0.792 | 0.487 | 0.603 | 19 | 20 | 5 | 26 |  |
| 0.44 | 0.435 | 0.750 | 0.474 | 0.581 | 18 | 20 | 6 | 26 |  |
| 0.45 | 0.391 | 0.708 | 0.486 | 0.576 | 17 | 18 | 7 | 28 |  |
| 0.46 | 0.391 | 0.667 | 0.471 | 0.552 | 16 | 18 | 8 | 28 |  |
| 0.47 | 0.370 | 0.667 | 0.485 | 0.561 | 16 | 17 | 8 | 29 |  |
| 0.48 | 0.348 | 0.667 | 0.500 | 0.571 | 16 | 16 | 8 | 30 |  |
| 0.49 | 0.326 | 0.625 | 0.500 | 0.556 | 15 | 15 | 9 | 31 |  |
| 0.50 | 0.304 | 0.625 | 0.517 | 0.566 | 15 | 14 | 9 | 32 |  |
| 0.51 | 0.304 | 0.625 | 0.517 | 0.566 | 15 | 14 | 9 | 32 |  |
| 0.52 | 0.283 | 0.583 | 0.519 | 0.549 | 14 | 13 | 10 | 33 |  |
| 0.53 | 0.261 | 0.583 | 0.538 | 0.560 | 14 | 12 | 10 | 34 |  |
| 0.54 | 0.239 | 0.583 | 0.560 | 0.571 | 14 | 11 | 10 | 35 |  |
|  **0.55** | 0.239 | 0.583 | 0.560 | 0.571 | 14 | 11 | 10 | 35 | Candidate A |
| 0.56 | 0.217 | 0.542 | 0.565 | 0.553 | 13 | 10 | 11 | 36 |  |
| 0.57 | 0.196 | 0.500 | 0.571 | 0.533 | 12 | 9 | 12 | 37 |  |
| 0.58 | 0.174 | 0.417 | 0.556 | 0.476 | 10 | 8 | 14 | 38 |  |
| 0.59 | 0.174 | 0.417 | 0.556 | 0.476 | 10 | 8 | 14 | 38 |  |
|  **0.60** | 0.152 | 0.417 | 0.588 | 0.488 | 10 | 7 | 14 | 39 | Candidate B |
| 0.61 | 0.130 | 0.417 | 0.625 | 0.500 | 10 | 6 | 14 | 40 |  |
| 0.62 | 0.109 | 0.417 | 0.667 | 0.513 | 10 | 5 | 14 | 41 |  |
| 0.63 | 0.087 | 0.417 | 0.714 | 0.526 | 10 | 4 | 14 | 42 |  |
| 0.64 | 0.087 | 0.417 | 0.714 | 0.526 | 10 | 4 | 14 | 42 |  |
| 0.65 | 0.065 | 0.417 | 0.769 | 0.541 | 10 | 3 | 14 | 43 |  |
| 0.66 | 0.065 | 0.417 | 0.769 | 0.541 | 10 | 3 | 14 | 43 |  |
| 0.67 | 0.065 | 0.417 | 0.769 | 0.541 | 10 | 3 | 14 | 43 |  |
| 0.68 | 0.065 | 0.375 | 0.750 | 0.500 | 9 | 3 | 15 | 43 |  |
| 0.69 | 0.065 | 0.375 | 0.750 | 0.500 | 9 | 3 | 15 | 43 |  |
| 0.70 | 0.065 | 0.375 | 0.750 | 0.500 | 9 | 3 | 15 | 43 |  |

## Focused Comparison: Current vs. Candidates

| | T = 0.39 (current) | T = 0.55 | T = 0.60 |
| :--- | :---: | :---: | :---: |
| **FPR (Human flagged)** | `0.522` | `0.239` | `0.152` |
| **Recall (AI caught)** | `0.875` | `0.583` | `0.417` |
| **Precision** | `0.467` | `0.560` | `0.588` |
| **F1** | `0.609` | `0.571` | `0.488` |

## Threshold Selection Objective

**Constraint:** FPR on human code must be <= 0.25 (at most 1 in 4 genuine 
human submissions flagged for review).

**Objective:** Among thresholds satisfying the FPR constraint, select the one 
that maximises F1 to balance recall and precision.

**Selected threshold:** `0.54`
- FPR = `0.239` (within <= 0.25 constraint)
- Recall = `0.583`
- Precision = `0.560`
- F1 = `0.571`

## Proposed Review Tiers (Three-Tier Policy)

| Tier | Score Range | Dashboard Label | Action |
| :--- | :---: | :--- | :--- |
| **Flagged** | `>= 0.54` | [!] Flagged for Review | Faculty should review for AI markers |
| **Inconclusive** | `[0.27, 0.54)` | [?] Inconclusive | Insufficient evidence to flag or clear |
| **Routine** | `< 0.27` | [OK] Routine Code | No action needed |

> The inconclusive tier explicitly communicates that the model cannot 
> confidently classify the submission. This prevents both false accusations 
> and false assurances.

## Generator-Specific Behaviour at Selected Threshold

- **codellama**: 8/18 caught (recall = 0.44)
- **gpt35**: 6/6 caught (recall = 1.00)
- **Human**: 11/46 false positives (FPR = 0.24)
