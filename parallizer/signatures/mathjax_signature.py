"""DSPy signature for identifying and completing MathJax equations within a document."""

from __future__ import annotations

import dspy


class MathJaxCompletion(dspy.Signature):
    """Detect incomplete math expressions and produce MathJax-compliant LaTeX completions."""

    current_document: str = dspy.InputField(
        desc=(
            "Full text of the document currently being edited. Include surrounding context "
            "for any inline or block math segments so the model can reason about missing pieces."
        )
    )
    # cursor_context: Optional[str] = dspy.InputField(
    #     optional=True,
    #     desc=(
    #         "Optional snippet (≤200 characters) around the editor cursor, with '<cursor>' marking "
    #         "the caret location. Provide when available to prioritize equations near the author’s focus."
    #     ),
    # )

    mathjax_equations: list[str] = dspy.OutputField(
        desc=(
            "List of MathJax-formatted equations (delimited with '$...$' or '$$...$$') that complete "
            "any partially written expressions found in the document. Preserve mathematical intent, ensure "
            "valid LaTeX syntax, and avoid duplicate or redundant equations."
        )
    )
    # notes: Optional[str] = dspy.OutputField(
    #     optional=True,
    #     desc=(
    #         "Optional guidance on how each completion relates to the original text, including assumptions "
    #         "made or ambiguities encountered while normalizing the equations."
    #     ),
    # )


__all__ = ["MathJaxCompletion"]


