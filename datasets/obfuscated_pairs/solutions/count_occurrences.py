def count_occurrences(arr, target):
    count = 0
    for item in arr:
        if item == target:
            count = count + 1
    return count
