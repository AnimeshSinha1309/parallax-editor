"""DSPy signatures supporting the Completion Agent (inline ghost text)."""

from __future__ import annotations

from typing import Optional

import dspy


class InlineCompletion(dspy.Signature):
    """Produce a low-latency inline completion tailored to Parallax's editor UX."""

    full_document: str = dspy.InputField(
        desc="Complete markdown document currently open in the editor."
    )
    cursor_context: str = dspy.InputField(
        desc=(
            "Window of text (≤150 characters) containing the literal marker '<cursor>' at the insertion point. "
        )
    )

    completion: str = dspy.OutputField(
        desc=(
            "Completion text that can be displayed inline. Preserve indentation relative to the '<cursor>' marker, "
            "avoid trailing explanations, and limit output to ≤6 lines to respect the ghost-text affordance."
        )
    )
    confidence: Optional[float] = dspy.OutputField(
        optional=True,
        desc=(
            "Optional confidence heuristic in the range [0, 1] used by the UI to adjust "
            "acceptance affordances."
        ),
    )


__all__ = ["GenerateInlineCompletion"]

