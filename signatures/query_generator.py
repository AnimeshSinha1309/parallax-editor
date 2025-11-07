"""DSPy signature for generating search queries to find related context files."""

from __future__ import annotations

import dspy


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


__all__ = ["RGQueryGenerator"]
