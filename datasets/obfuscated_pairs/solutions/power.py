def power(base, exp):
    result = 1
    for i in range(exp):
        result = result * base
    return result
