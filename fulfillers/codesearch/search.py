"""Main SDK interface for code search."""

from typing import Optional, List, Tuple, Any

from ..base import Fulfiller
from ..models import Card, CardType, GlobalPreferenceContext
from utils.ripgrep import RipgrepSearch, SearchResult, SearchMatch
from utils.context import PreferenceContext


class CodeSearch(Fulfiller):
    """
    Main SDK interface for code search.

    Currently wraps RipgrepSearch directly.
    Simple, no fallback logic needed.

    Usage:
        # Search with explicit directory
        search = CodeSearch()
        result = await search.search("def.*retry", "/path/to/code")

        # Search using context (auto-discovers git repo)
        search = CodeSearch()
        result = await search.search("def.*retry")

        # Search with custom context
        context = PreferenceContext()
        context.add_path("/path/to/code")
        search = CodeSearch(context=context)
        result = await search.search("def.*retry")

        for match in result.matches:
            print(f"{match.file_path}:{match.line_number}")
    """

    def __init__(
        self,
        context: Optional[PreferenceContext] = None,
        max_results: int = 50,
        context_lines: int = 2,
        case_sensitive: bool = False,
    ):
        """
        Initialize CodeSearch with an optional context and default search parameters.

        Args:
            context: PreferenceContext defining which directories/files to search.
                    If None, context will be auto-created when needed.
            max_results: Default maximum matches to return (default 50)
            context_lines: Default lines of context before/after match (default 2)
            case_sensitive: Default case sensitivity (default False)
        """
        self.backend = RipgrepSearch(context=context)
        self.default_max_results = max_results
        self.default_context_lines = context_lines
        self.default_case_sensitive = case_sensitive

    async def invoke(
        self,
        document_text: str,
        cursor_position: Tuple[int, int],
        global_context: GlobalPreferenceContext,
        intent_label: Optional[str] = None,
        **kwargs
    ) -> List[Card]:
        """
        Invoke code search fulfiller.

        Args:
            document_text: The entire text content of the current document (currently unused)
            cursor_position: (line, column) position of the cursor (currently unused)
            global_context: Global preference context containing scope root and plan path
            intent_label: Optional search query/pattern to look for
            **kwargs: Additional search parameters (max_results, context_lines, case_sensitive, query)

        Returns:
            List of Card objects with search results
        """
        # Extract search parameters from kwargs or use defaults
        max_results = kwargs.get('max_results', self.default_max_results)
        context_lines = kwargs.get('context_lines', self.default_context_lines)
        case_sensitive = kwargs.get('case_sensitive', self.default_case_sensitive)

        # Use scope_root from global_context as the directory to search
        directory = kwargs.get('directory', global_context.scope_root)

        # Use intent_label or 'query' kwarg as the search query
        query = kwargs.get('query', intent_label)
        if not query:
            return [Card(
                header="No Query",
                text="No search query provided",
                type=CardType.CONTEXT,
                metadata={"error": "missing_query"}
            )]

        # Perform the search
        result = await self.search(
            query=query,
            directory=directory,
            max_results=max_results,
            context_lines=context_lines,
            case_sensitive=case_sensitive,
        )

        # Convert SearchResult to List[Card]
        return self._convert_to_cards(result)

    def _convert_to_cards(self, result: SearchResult) -> List[Card]:
        """Convert SearchResult to a list of Card objects."""
        if not result.success:
            return [Card(
                header="Search Error",
                text=result.error or "Unknown error occurred",
                type=CardType.CONTEXT,
                metadata={"query": result.query, "success": False}
            )]

        if not result.matches:
            return [Card(
                header="No Results",
                text=f"No matches found for: {result.query}",
                type=CardType.CONTEXT,
                metadata={"query": result.query, "total_matches": 0}
            )]

        cards = []
        for match in result.matches:
            # Format the card text with context
            text_lines = []
            if match.context_before:
                text_lines.extend([f"  {line}" for line in match.context_before])
            text_lines.append(f"> {match.line_content}")
            if match.context_after:
                text_lines.extend([f"  {line}" for line in match.context_after])

            card = Card(
                header=f"{match.file_path}:{match.line_number}",
                text="\n".join(text_lines),
                type=CardType.CONTEXT,
                metadata={
                    "file_path": match.file_path,
                    "line_number": match.line_number,
                    "query": result.query,
                }
            )
            cards.append(card)

        return cards

    async def search(
        self,
        query: str,
        directory: Optional[str] = None,
        max_results: Optional[int] = None,
        context_lines: Optional[int] = None,
        case_sensitive: Optional[bool] = None,
    ) -> SearchResult:
        """
        Search for code patterns.

        Args:
            query: Regex pattern to search for
            directory: Directory to search in. If None, uses paths from context.
            max_results: Maximum matches to return (uses default if None)
            context_lines: Lines of context before/after match (uses default if None)
            case_sensitive: Whether search is case-sensitive (uses default if None)

        Returns:
            SearchResult with matches and metadata

        Examples:
            # Search with explicit directory
            result = await search.search("def main", ".", max_results=10)

            # Search using context (auto-discovers git repo)
            result = await search.search("def main", max_results=10)

            if result.success:
                print(f"Found {result.total_matches} matches")
        """
        # Use defaults if not specified
        if max_results is None:
            max_results = self.default_max_results
        if context_lines is None:
            context_lines = self.default_context_lines
        if case_sensitive is None:
            case_sensitive = self.default_case_sensitive

        return await self.backend.search(
            query, directory, max_results, context_lines, case_sensitive
        )

    async def is_available(self) -> bool:
        """Check if ripgrep is installed."""
        return await self.backend.is_available()
