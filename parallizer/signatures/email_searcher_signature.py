"""DSPy signature for searching emails relevant to current plan document."""

from __future__ import annotations

from typing import List

import dspy


class EmailSearcher(dspy.Signature):
    """Search mailbox data for emails contextually relevant to the current plan document."""

    mailbox_data: List[str] = dspy.InputField(
        desc="List of all emails currently indexed from the mailbox."
    )
    current_plan_document: str = dspy.InputField(
        desc="Latest high-level plan or task document describing the intended changes."
    )

    relevant_emails: List[str] = dspy.OutputField(
        desc=(
            "1 to 2 emails selected from mailbox_data which seem contextually relevant "
            "to the current_plan_document. Return the most relevant emails that provide "
            "useful context for the current task or plan. If no emails feel related, or even if they "
            "don't have a specific word match, feel free to return 0 emails as well."
        )
    )


__all__ = ["EmailSearcher"]
