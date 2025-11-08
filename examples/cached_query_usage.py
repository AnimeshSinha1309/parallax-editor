"""
Example usage of cached query generators.

This demonstrates how to use the cached predictor functions to reduce
redundant LLM calls for identical queries.
"""

import dspy
from signatures import create_cached_rg_predictor, create_cached_web_predictor
from utils.query_cache import clear_all_caches


def example_rg_query_with_cache():
    """Example: Using cached RGQueryGenerator."""

    # Create a cached predictor instance
    predictor = create_cached_rg_predictor()

    # First call - hits the LLM
    result1 = predictor(
        current_document="import React from 'react'",
        repo_summary="A React-based web application"
    )
    print("First call (LLM):", result1.queries)

    # Second call with same inputs - retrieves from cache
    result2 = predictor(
        current_document="import React from 'react'",
        repo_summary="A React-based web application"
    )
    print("Second call (cached):", result2.queries)

    # Different inputs - hits the LLM again
    result3 = predictor(
        current_document="import numpy as np",
        repo_summary="A Python data science project"
    )
    print("Third call (LLM):", result3.queries)


def example_web_query_with_cache():
    """Example: Using cached WebQueryGenerator."""

    # Create a cached predictor instance
    predictor = create_cached_web_predictor()

    # First call - hits the LLM
    result1 = predictor(
        current_document="const app = express()",
        context_description="Building an Express.js REST API"
    )
    print("First call (LLM):", result1.queries)

    # Second call with same inputs - retrieves from cache
    result2 = predictor(
        current_document="const app = express()",
        context_description="Building an Express.js REST API"
    )
    print("Second call (cached):", result2.queries)


def example_cache_management():
    """Example: Managing the query cache."""

    # Check cache size
    from utils.query_cache import get_rg_query_cache, get_web_query_cache

    rg_cache = get_rg_query_cache()
    web_cache = get_web_query_cache()

    print(f"RG cache size: {len(rg_cache)}")
    print(f"Web cache size: {len(web_cache)}")

    # Clear all caches
    clear_all_caches()
    print("Caches cleared")

    print(f"RG cache size after clear: {len(rg_cache)}")
    print(f"Web cache size after clear: {len(web_cache)}")


if __name__ == "__main__":
    # Note: These examples require DSPy to be configured with a language model
    # dspy.configure(lm=your_language_model)

    print("=== RG Query Generator with Cache ===")
    example_rg_query_with_cache()

    print("\n=== Web Query Generator with Cache ===")
    example_web_query_with_cache()

    print("\n=== Cache Management ===")
    example_cache_management()
