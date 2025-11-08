"""DSPy signature for generating search queries to find related context files."""

from __future__ import annotations

import dspy
from utils.query_cache import cached_predictor, get_rg_query_cache


class RGQueryGenerator(dspy.Signature):
    """Generate ripgrep or semantic search queries to find related context files."""

    current_document: str = dspy.InputField(
        desc="The document currently being edited or viewed in the editor."
    )
    repo_summary: str = dspy.InputField(
        desc=(
            "Summary, README, or high-level description of the repository structure "
            "and purpose to help understand the codebase context."
        )
    )

    queries: list[str] = dspy.OutputField(
        desc=(
            "List of ripgrep queries (regex patterns) or semantic search queries "
            "to identify related files in the repository. Each query should target "
            "specific code patterns, imports, function names, or concepts that would "
            "help provide relevant context for the current document."
        )
    )


def create_cached_predictor():
    """
    Create a cached predictor for RGQueryGenerator.

    This predictor automatically caches results based on input parameters,
    significantly reducing redundant LLM calls for identical queries.

    Returns:
        Cached DSPy predictor instance

    Example:
        >>> predictor = create_cached_predictor()
        >>> result = predictor(current_document=doc, repo_summary=summary)
    """
    base_predictor = dspy.Predict(RGQueryGenerator)
    return cached_predictor(get_rg_query_cache())(base_predictor)


__all__ = ["RGQueryGenerator", "create_cached_predictor"]
