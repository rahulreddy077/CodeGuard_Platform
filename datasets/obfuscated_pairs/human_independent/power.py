def power(base, exp):
    if exp == 0:
        return 1
    if exp < 0:
        return 1 / power(base, -exp)
    half = power(base, exp // 2)
    if exp % 2 == 0:
        return half * half
    return base * half * half
