"""Abstract base class for all fulfillers."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from .models import Card


class Fulfiller(ABC):
    """
    Abstract base class for all fulfiller implementations.

    A fulfiller takes user context (document text, parser position, scope root)
    and optionally an intent label, then returns a list of cards with relevant information.

    Examples of fulfillers:
    - CodeSearch: Returns cards with code search results
    - Documentation: Returns cards with relevant documentation
    - ContextAgent: Returns cards with contextual suggestions
    """

    @abstractmethod
    async def invoke(
        self,
        document_text: str,
        parser_position: Tuple[int, int],
        scope_root: str,
        intent_label: Optional[str] = None,
        **kwargs
    ) -> List[Card]:
        """
        Invoke the fulfiller with the given inputs.

        Args:
            document_text: The entire text content of the current document as a string
            parser_position: (line, column) position of the parser/cursor
            scope_root: Root directory path for the scope
            intent_label: Optional LLM-generated intent or label describing the query
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
