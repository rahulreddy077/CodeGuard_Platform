def compute_gcd(x, y):
    while y != 0:
        temp = x % y
        x = y
        y = temp
    return x
