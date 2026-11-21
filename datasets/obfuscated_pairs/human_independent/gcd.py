def gcd(a, b):
    a_val, b_val = abs(a), abs(b)
    while b_val:
        a_val, b_val = b_val, a_val % b_val
    return a_val
