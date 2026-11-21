def reverse_string(s):
    res = []
    for char in s:
        res.insert(0, char)
    return "".join(res)
