def remove_duplicates(arr):
    seen = []
    for item in arr:
        if item not in seen:
            seen.append(item)
    return seen
