def flatten_list(nested):
    output = []
    stack = [nested]
    while stack:
        curr = stack.pop(0)
        if isinstance(curr, list):
            stack = curr + stack
        else:
            output.append(curr)
    return output
