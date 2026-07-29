def compute_quality_metrics(code: str) -> dict:
    """
    Calculates code quality, complexity, and maintainability metrics.
    """
    lines = code.splitlines()
    num_lines = len(lines)
    comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
    empty_lines = sum(1 for line in lines if not line.strip())
    
    # Calculate simple comment ratio
    comment_ratio = comment_lines / num_lines if num_lines > 0 else 0.0
    
    return {
        "loc": num_lines,
        "comment_lines": comment_lines,
        "empty_lines": empty_lines,
        "comment_ratio": round(comment_ratio, 4),
        "complexity_level": "Low" if num_lines < 100 else "Medium" if num_lines < 300 else "High"
    }
