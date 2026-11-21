def sum_digits(n):
    total = 0
    num = abs(n)
    while num > 0:
        total += num % 10
        num //= 10
    return total
