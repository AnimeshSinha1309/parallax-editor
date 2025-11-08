"""DSPy signature for identifying questions and ambiguities in plan documents."""

from __future__ import annotations

import dspy


class QuestionAmbiguityIdentifier(dspy.Signature):
    """Identify potential ambiguities and questions that arise from analyzing a plan document against relevant code context."""

    relevant_code_context: str = dspy.InputField(
        desc=(
            "Relevant code snippets, file structures, or implementation details "
            "from the codebase that relate to the current plan. This provides "
            "the technical context needed to evaluate the plan's feasibility and clarity."
        )
    )
    current_plan: str = dspy.InputField(
        desc=(
            "The current plan document being analyzed. This may be a design doc, "
            "feature specification, implementation roadmap, or other planning artifact "
            "that needs to be validated against the existing codebase."
        )
    )

    output_ambiguities_questions: list[str] = dspy.OutputField(
        desc=(
            "List of questions and ambiguities identified in the plan. Each item should be "
            "a clear, actionable question or identified ambiguity that needs clarification. "
            "Examples: 'How should error handling work when X fails?', "
            "'The plan mentions using library Y but the codebase uses Z', "
            "'What happens if condition A occurs during step 3?'. "
            "These will be used to create cards for team discussion and resolution."
        )
    )


__all__ = ["QuestionAmbiguityIdentifier"]
