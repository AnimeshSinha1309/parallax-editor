"""Dummy fulfiller for placeholder content during development."""

import random
from typing import List, Tuple, Any, Optional

from .base import Fulfiller
from .models import Card, CardType


class DummyFulfiller(Fulfiller):
    """
    A dummy fulfiller that returns placeholder content.

    This fulfiller is used during development to generate sample cards
    without requiring actual LLM API calls. It returns a mix of QUESTION,
    CONTEXT, and COMPLETION type cards.

    TODO: Replace with actual LLM-powered fulfillers in production.
    """

    async def invoke(
        self,
        text_buffer: str,
        cursor_position: Tuple[int, int],
        query_intent: str,
        context: Optional[Any] = None,
        **kwargs
    ) -> List[Card]:
        """
        Generate dummy cards of various types.

        Args:
            text_buffer: Current file content (unused in dummy implementation)
            cursor_position: Cursor position (unused in dummy implementation)
            query_intent: Intent or trigger reason (unused in dummy implementation)
            context: Optional context (unused in dummy implementation)
            **kwargs: Additional parameters

        Returns:
            List of 1-3 random placeholder cards
        """
        all_cards = [
            # CONTEXT cards - contextual information
            Card(
                header="Code Suggestion",
                text="Consider adding type hints to improve code clarity and catch type-related bugs early.",
                type=CardType.CONTEXT,
                metadata={"source": "dummy"}
            ),
            Card(
                header="Refactoring Tip",
                text="This function is getting long. Consider breaking it into smaller, more focused functions.",
                type=CardType.CONTEXT,
                metadata={"source": "dummy"}
            ),
            Card(
                header="Best Practice",
                text="Add docstrings to your functions to improve code documentation and maintainability.",
                type=CardType.CONTEXT,
                metadata={"source": "dummy"}
            ),
            Card(
                header="Performance Tip",
                text="Consider using list comprehensions instead of loops for better performance and readability.",
                type=CardType.CONTEXT,
                metadata={"source": "dummy"}
            ),
            Card(
                header="Style Guide",
                text="Follow PEP 8 conventions for consistent code formatting across your project.",
                type=CardType.CONTEXT,
                metadata={"source": "dummy"}
            ),

            # QUESTION cards - clarifying questions
            Card(
                header="Clarification Needed",
                text="Should this function handle empty input? What should the return value be in that case?",
                type=CardType.QUESTION,
                metadata={"source": "dummy"}
            ),
            Card(
                header="Design Question",
                text="Do you want this to be synchronous or asynchronous? Consider the performance implications.",
                type=CardType.QUESTION,
                metadata={"source": "dummy"}
            ),
            Card(
                header="Testing Strategy",
                text="How should we test this component? Unit tests, integration tests, or both?",
                type=CardType.QUESTION,
                metadata={"source": "dummy"}
            ),

            # COMPLETION cards - inline completion suggestions
            Card(
                header="Inline Completion",
                text="    return result if result is not None else default_value",
                type=CardType.COMPLETION,
                metadata={"source": "dummy", "trigger": "ghost_text"}
            ),
            Card(
                header="Inline Completion",
                text="    # TODO: Implement error handling for edge cases",
                type=CardType.COMPLETION,
                metadata={"source": "dummy", "trigger": "ghost_text"}
            ),
            Card(
                header="Inline Completion",
                text='    logger.debug(f"Processing {len(items)} items")',
                type=CardType.COMPLETION,
                metadata={"source": "dummy", "trigger": "ghost_text"}
            ),
        ]

        # Return 1-3 random cards
        num_cards = random.randint(1, 3)
        return random.sample(all_cards, num_cards)

    async def is_available(self) -> bool:
        """
        Check if dummy fulfiller is available.

        Returns:
            Always returns True since this is a dummy implementation
        """
        return True
