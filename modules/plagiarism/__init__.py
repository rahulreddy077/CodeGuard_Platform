def detect_plagiarism(code_a: str, code_b: str) -> dict:
    """
    Compares two code snippets and returns a plagiarism report.
    This is a baseline implementation that computes string similarity.
    """
    # Simple Jaccard similarity of words as placeholder
    set_a = set(code_a.split())
    set_b = set(code_b.split())
    if not set_a or not set_b:
        return {"similarity_score": 0.0, "matches": []}
    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)
    score = len(intersection) / len(union)
    return {
        "similarity_score": round(score, 4),
        "matches": list(intersection)[:10]  # Return up to 10 matching words as matches
    }
