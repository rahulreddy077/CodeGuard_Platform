def find_second_largest(nums):
    unique_sorted = sorted(list(set(nums)))
    if len(unique_sorted) < 2:
        return None
    return unique_sorted[-2]
