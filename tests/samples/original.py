def compute_gcd(x, y):
    """
    Computes the greatest common divisor of two numbers using Euclidean algorithm.
    """
    # Keep looping until y becomes zero
    while y != 0:
        temp = x % y
        x = y
        y = temp
    return x
