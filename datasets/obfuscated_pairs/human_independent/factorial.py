def factorial(n):
    if n <= 1:
        return 1
    accum = 1
    for step in range(2, n + 1):
        accum *= step
    return accum
