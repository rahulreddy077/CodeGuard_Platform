def is_armstrong(n):
    # Calculate the sum of the cubes of each digit
    sum = 0
    for digit in str(n):
        sum += int(digit) ** 3
    # Check if the sum is equal to the original number
    return sum == n