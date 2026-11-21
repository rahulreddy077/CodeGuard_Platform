def is_anagram(s1, s2):
    a = sorted(s1.replace(" ", "").lower())
    b = sorted(s2.replace(" ", "").lower())
    return a == b
