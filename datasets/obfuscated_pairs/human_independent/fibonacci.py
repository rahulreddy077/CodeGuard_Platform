def fibonacci(n):
    if n <= 0:
        return 0
    if n == 1:
        return 1
    seq = [0, 1]
    for _ in range(2, n + 1):
        seq.append(seq[-1] + seq[-2])
    return seq[n]
