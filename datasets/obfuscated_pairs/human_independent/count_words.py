def count_words(sentence):
    if not sentence or not sentence.strip():
        return 0
    words_list = [w for w in sentence.strip().split() if len(w) > 0]
    return len(words_list)
