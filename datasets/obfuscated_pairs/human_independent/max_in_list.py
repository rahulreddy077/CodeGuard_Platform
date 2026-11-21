def max_in_list(nums):
    if not nums:
        return None
    curr_max = nums[0]
    for element in nums[1:]:
        if element > curr_max:
            curr_max = element
    return curr_max
