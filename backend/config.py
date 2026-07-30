# Centralized Configuration for CodeGuard Analysis Engine

SIMILARITY_CONFIG = {
    "embedding": 0.70,     # Weight for GraphCodeBERT embedding similarity
    "jaccard": 0.20,       # Weight for structural fingerprint Jaccard index
    "tree_edit": 0.10,     # Weight for AST Tree Edit Distance similarity
    "threshold": 0.85,     # Threshold above which matching is flagged as plagiarism
    "top_k": 5             # Candidate search size limit
}
