"""DSPy signature for generating web search queries to find external context."""

from __future__ import annotations

import dspy


class WebQueryGenerator(dspy.Signature):
    """Generate web search queries to find relevant external context and documentation."""

    current_document: str = dspy.InputField(
        desc="The document currently being edited or viewed in the editor."
    )
    context_description: str = dspy.InputField(
        desc=(
            "High-level description of the context, task, or domain that the user "
            "is working on. This helps target web searches to relevant documentation, "
            "tutorials, API references, or technical resources."
        )
    )

    queries: list[str] = dspy.OutputField(
        desc=(
            "List of web search queries optimized for finding relevant external context. "
            "Each query should target specific documentation, API references, tutorials, "
            "Stack Overflow discussions, or technical articles that would help provide "
            "context for the current document. Prioritize authoritative sources and "
            "official documentation when applicable."
        )
    )


__all__ = ["WebQueryGenerator"]
