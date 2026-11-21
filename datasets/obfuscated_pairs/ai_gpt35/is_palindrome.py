def is_palindrome(text: str) -> bool:
    """Checks whether string is a palindrome ignoring case and non-alphanumeric chars."""
    filtered = [ch.lower() for ch in text if ch.isalnum()]
    return filtered == filtered[::-1]
