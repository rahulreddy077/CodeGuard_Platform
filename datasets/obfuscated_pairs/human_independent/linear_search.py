def linear_search(arr, target):
    for idx, val in enumerate(arr):
        if val == target:
            return idx
    return -1
