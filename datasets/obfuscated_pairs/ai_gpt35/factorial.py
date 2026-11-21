def factorial(n: int) -> int:
    """Calculates non-negative integer factorial."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    return 1 if n <= 1 else n * factorial(n - 1)
