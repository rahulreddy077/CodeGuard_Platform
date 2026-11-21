def bubble_sort(arr):
    swapped = True
    end = len(arr) - 1
    while swapped:
        swapped = False
        for idx in range(end):
            if arr[idx] > arr[idx + 1]:
                arr[idx], arr[idx + 1] = arr[idx + 1], arr[idx]
                swapped = True
        end -= 1
    return arr
