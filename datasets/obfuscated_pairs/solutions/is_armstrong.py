def is_armstrong(n):
    digits = str(n)
    power_val = len(digits)
    total = 0
    for d in digits:
        total = total + int(d) ** power_val
    return total == n
