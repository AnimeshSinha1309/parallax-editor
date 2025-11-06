"""Abstract base class for code search backends."""

from abc import ABC, abstractmethod
from .models import SearchResult


class CodeSearchBackend(ABC):
    """
    Abstract base class for code search implementations.

    Currently only RipgrepSearch is implemented.
    Future: HoundSearch, SemanticSearch, etc.
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        directory: str,
        max_results: int = 50,
        context_lines: int = 2,
        case_sensitive: bool = False,
    ) -> SearchResult:
        """Execute search and return results."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this backend is available."""
        pass
