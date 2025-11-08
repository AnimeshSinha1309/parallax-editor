# Test Document for Backend API Testing

## Introduction

This is a test document for validating the Parallizer backend API. It contains various code snippets and text to trigger different fulfillers.

## Python Code Example

Here's a simple Python function:

```python
def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# Usage
result = calculate_fibonacci(10)
print(f"The 10th Fibonacci number is: {result}")
```

## TODO Items

- [ ] Implement error handling for edge cases
- [ ] Add unit tests for the fibonacci function
- [ ] Optimize the recursive implementation
- [ ] Consider using memoization

## Questions and Ambiguities

How should we handle negative input values? Should we raise an exception or return a default value?

What's the best way to optimize this recursive implementation for large values of n?

## Next Steps

We need to refactor this code to use an iterative approach instead of recursion for better performance.

---

**Note**: This document is intentionally simple to keep test execution fast while still triggering all fulfiller types.
