def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left_part = merge_sort(arr[:mid])
    right_part = merge_sort(arr[mid:])
    
    merged = []
    p1 = p2 = 0
    while p1 < len(left_part) and p2 < len(right_part):
        if left_part[p1] <= right_part[p2]:
            merged.append(left_part[p1])
            p1 += 1
        else:
            merged.append(right_part[p2])
            p2 += 1
    merged.extend(left_part[p1:])
    merged.extend(right_part[p2:])
    return merged
