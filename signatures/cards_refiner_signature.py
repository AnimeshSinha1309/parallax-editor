"""DSPy signature for refining and stabilizing card displays across updates."""

from __future__ import annotations

import dspy


class CardsRefiner(dspy.Signature):
    """Refine card display by merging old and new cards to minimize UI disruption."""

    existing_cards: str = dspy.InputField(
        desc=(
            "JSON array of currently displayed cards. Each card has 'header' (title), "
            "'text' (main content), and 'metadata' (additional info). These cards "
            "represent the user's current view and should be preserved when semantically "
            "similar to new proposals to avoid disruptive UI disruption."
        )
    )
    newly_proposed_cards: str = dspy.InputField(
        desc=(
            "JSON array of newly proposed cards from the latest context update. "
            "Each card has 'header', 'text', and 'metadata' fields. These represent "
            "fresh results that may contain updated or new information."
        )
    )

    refined_cards: str = dspy.OutputField(
        desc=(
            "JSON array of the final cards to display, ordered by perceived importance. "
            "Retain existing cards when they are semantically similar to newly proposed cards "
            "to minimize UI disruption. Include new cards that provide distinct value. "
            "Remove cards that are no longer relevant. The count may differ from input sets. "
            "Each card must maintain the structure: {'header': str, 'text': str, 'metadata': dict}.")
    )


__all__ = ["CardsRefiner"]
