def flatten_list(nested):
    flattened = []
    for item in nested:
        if isinstance(item, list):
            flattened.extend(flatten_list(item))
        else:
            flattened.append(item)
    return flattened