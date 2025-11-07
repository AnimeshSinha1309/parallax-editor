"""Abstract base class for all fulfillers."""

from abc import ABC, abstractmethod
from typing import List, Any, Optional, Tuple


class Fulfiller(ABC):
    """
    Abstract base class for all fulfiller implementations.

    A fulfiller takes user context (text buffer, cursor position, query intent)
    and returns a list of cards with relevant information.

    Examples of fulfillers:
    - CodeSearch: Returns cards with code search results
    - Documentation: Returns cards with relevant documentation
    - ContextAgent: Returns cards with contextual suggestions
    """

    @abstractmethod
    async def invoke(
        self,
        text_buffer: str,
        cursor_position: Tuple[int, int],
        query_intent: str,
        context: Optional[Any] = None,
        **kwargs
    ) -> List["Card"]:
        """
        Invoke the fulfiller with the given inputs.

        Args:
            text_buffer: All text in the current file as a string
            cursor_position: (line, column) position of the cursor
            query_intent: LLM-generated intent or note behind the query
            context: Optional context object (fulfiller-specific)
            **kwargs: Additional fulfiller-specific parameters

        Returns:
            List of Card objects containing the results
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if this fulfiller is available and ready to use.

        Returns:
            True if the fulfiller can be invoked, False otherwise
        """
        pass
