def count_occurrences(arr, target):
    total = 0
    i = 0
    while i < len(arr):
        if arr[i] == target:
            total += 1
        i += 1
    return total
