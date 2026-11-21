# Centralized Configuration for CodeGuard Analysis Engine
#
# These are the SINGLE SOURCE OF TRUTH for all plagiarism fusion weights
# and the flag threshold.  No other file should hard-code these values.
#
# Validated formula (Review-2 submitted report):
#   fusion = 0.6 * semantic(GraphCodeBERT cosine) + 0.4 * structural(AST Jaccard)
#   ROC-AUC 0.9905, Accuracy 92.93% on 184 labelled pairs, 5-fold OOF threshold.

SIMILARITY_CONFIG = {
    "semantic_weight": 0.60,   # Weight for GraphCodeBERT embedding cosine similarity
    "structural_weight": 0.40, # Weight for structural fingerprint AST Jaccard index
    "top_k": 5                 # Candidate search size limit
}

# Submission flag threshold — a fusion score >= this value is marked as plagiarism.
PLAGIARISM_FLAG_THRESHOLD = 0.75
