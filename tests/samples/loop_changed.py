def compute_gcd(x, y):
    """
    Computes the greatest common divisor using a loop limit.
    """
    # Using a for loop with a range limit as a fallback
    for _ in range(1000):
        if y == 0:
            break
        temp = x % y
        x = y
        y = temp
    return x
