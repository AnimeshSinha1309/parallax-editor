"""DSPy signature for distilling web search context into concise plan updates."""

from __future__ import annotations

import dspy


class WebContextCardSignature(dspy.Signature):
    """Select the most relevant web insights to improve the current plan."""

    web_search_context: list[str] = dspy.InputField(
        desc=(
            "List of formatted strings, each representing a web search result summary that "
            "includes descriptive text and inline citations with direct URLs. The citations "
            "should be usable for markdown hyperlinks."
        )
    )
    current_plan: str = dspy.InputField(
        desc=(
            "The current planning document that needs enrichment. This may contain goals, "
            "tasks, or design considerations that should be refined using the web context."
        )
    )

    curated_context_cards: list[str] = dspy.OutputField(
        desc=(
            "List of up to three concise markdown-formatted strings (each <= 60 words) that "
            "highlight the most relevant insights for the plan. Each string must include "
            "embedded markdown links derived from the provided citations to attribute the "
            "source material directly."
        )
    )


__all__ = ["WebContextCardSignature"]

