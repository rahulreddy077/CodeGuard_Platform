def is_anagram(s1, s2):
    c1, c2 = {}, {}
    for char in s1.lower().replace(" ", ""):
        c1[char] = c1.get(char, 0) + 1
    for char in s2.lower().replace(" ", ""):
        c2[char] = c2.get(char, 0) + 1
    return c1 == c2
