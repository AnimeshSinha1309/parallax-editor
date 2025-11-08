"""DSPy signature for summarizing scoped codebases and plans."""

from __future__ import annotations

import dspy


class CodebaseSummary(dspy.Signature):
    """Summarize the intent and purpose of a scoped repository segment."""

    current_plan_document: str = dspy.InputField(
        desc=(
            "Latest high-level plan or task document describing the intended changes "
            "or goals for this scope. Include numbered steps, notes, and any context "
            "that clarifies what is being attempted."
        )
    )
    scope_tree_structure: str = dspy.InputField(
        desc=(
            "Textual tree representation of the repository or scoped directory. "
            "Include directory hierarchy and file names to expose overall structure "
            "and important entry points."
        )
    )
    scope_readme: str = dspy.InputField(
        desc=(
            "Contents of the README file located in the scoped directory, if present. "
            "Pass an empty string when no README exists."
        )
    )

    summary_markdown: str = dspy.OutputField(
        desc=(
            "Single markdown-formatted paragraph or list that concisely explains the "
            "primary intent of the scoped repository segment, how the current plan "
            "relates to that intent, and the overall purpose of the codebase."
        )
    )


__all__ = ["CodebaseSummary"]

