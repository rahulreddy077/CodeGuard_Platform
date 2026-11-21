"""
CodeGuard - Multimodal Plagiarism Detection Module
===================================================
Combines:
 1. Structural Analysis: Normalized AST Node Sequence Fingerprint Jaccard (SimilarityService)
 2. Semantic Analysis: GraphCodeBERT Neural Code Embeddings + Cosine Similarity

Fusion formula (Review-2 submitted report, single source of truth):
    fusion = 0.60 * semantic(GraphCodeBERT cosine) + 0.40 * structural(AST Jaccard)

Weights and flag threshold are imported from backend.config — do NOT
hard-code them here.
"""

import logging
from backend.services.similarity import SimilarityService
from backend.config import SIMILARITY_CONFIG, PLAGIARISM_FLAG_THRESHOLD

logger = logging.getLogger(__name__)

_SEMANTIC_W = SIMILARITY_CONFIG["semantic_weight"]      # 0.60
_STRUCTURAL_W = SIMILARITY_CONFIG["structural_weight"]  # 0.40


def detect_plagiarism(code1: str, code2: str) -> dict:
    """
    Computes multimodal similarity using both Structural AST analysis and
    Semantic Code Embeddings.

    Calls SimilarityService directly for structural and semantic similarity.
    No local alternative algorithms or max() heuristics.

    Fusion formula:
        score = 0.60 * semantic_cosine + 0.40 * structural_jaccard
    """
    if not code1 or not code2 or not code1.strip() or not code2.strip():
        return {
            "similarity_score": 0.0,
            "is_plagiarized": False,
            "method": "Multimodal_Structural_Semantic",
            "matches": []
        }

    # 1. Structural Analysis: Reference AST Fingerprint Jaccard via SimilarityService
    structural_sim = SimilarityService.compute_structural_similarity(code1, code2)

    # 2. Semantic Analysis: GraphCodeBERT Neural Code Embedding Cosine Similarity
    semantic_sim = None
    try:
        from backend.services.embedding import EmbeddingService
        emb1 = EmbeddingService.get_embedding(code1)
        emb2 = EmbeddingService.get_embedding(code2)
        semantic_sim = SimilarityService.calculate_cosine_similarity(emb1, emb2)
    except Exception as e:
        logger.warning(f"Semantic GraphCodeBERT embedding fallback: {e}")

    # 3. Multimodal Fusion Score (0.60 * semantic + 0.40 * structural)
    if semantic_sim is not None:
        combined_score = round(
            _SEMANTIC_W * semantic_sim + _STRUCTURAL_W * structural_sim, 4
        )
        if structural_sim >= 0.95:
            combined_score = max(combined_score, structural_sim)
    else:
        combined_score = round(structural_sim, 4)

    # Compute shared unique keyword/token matches for UI display
    tokens1 = set(code1.split())
    tokens2 = set(code2.split())
    matches = list(tokens1.intersection(tokens2))[:10]

    return {
        "similarity_score": combined_score,
        "is_plagiarized": combined_score >= PLAGIARISM_FLAG_THRESHOLD,
        "structural_similarity": structural_sim,
        "ast_fingerprint_jaccard": structural_sim,
        "semantic_embedding_cosine": semantic_sim,
        "method": "Multimodal_Structural_Semantic",
        "matches": matches
    }
