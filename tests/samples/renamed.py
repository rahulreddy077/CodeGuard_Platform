def find_divisor(val1, val2):
    """
    Calculates the divisor.
    """
    # loop logic
    while val2 != 0:
        remainder = val1 % val2
        val1 = val2
        val2 = remainder
    return val1
