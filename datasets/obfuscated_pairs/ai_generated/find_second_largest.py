def find_second_largest(nums):
    # Sort the list in descending order
    nums.sort(reverse=True)
    # Return the second largest element
    return nums[1]