"""Dummy fulfiller for placeholder content during development."""

import random
import logging
from typing import List, Tuple, Any, Optional

from fulfillers.base import Fulfiller
from fulfillers.models import Card, CardType
from utils.context import GlobalPreferenceContext

logger = logging.getLogger("parallax.dummy_fulfiller")


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
        document_text: str,
        cursor_position: Tuple[int, int],
        global_context: GlobalPreferenceContext,
        intent_label: Optional[str] = None,
        **kwargs
    ) -> List[Card]:
        """
        Generate dummy cards of various types.

        Args:
            document_text: Current file content (unused in dummy implementation)
            cursor_position: Cursor position (unused in dummy implementation)
            global_context: Global preference context (unused in dummy implementation)
            intent_label: Optional intent label (unused in dummy implementation)
            **kwargs: Additional parameters

        Returns:
            List of 1-3 random placeholder cards
        """
        logger.info(f"DummyFulfiller invoked at {cursor_position}, scope_root={global_context.scope_root}, plan_path={global_context.plan_path}")
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
        selected_cards = random.sample(all_cards, num_cards)
        logger.debug(f"DummyFulfiller returning {num_cards} cards: {[c.type.value for c in selected_cards]}")
        return selected_cards

    async def is_available(self) -> bool:
        """
        Check if dummy fulfiller is available.

        Returns:
            Always returns True since this is a dummy implementation
        """
        logger.debug("DummyFulfiller is always available")
        return True
