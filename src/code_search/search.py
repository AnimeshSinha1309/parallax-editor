"""Main SDK interface for code search."""

from .ripgrep import RipgrepSearch
from .models import SearchResult


class CodeSearch:
    """
    Main SDK interface for code search.

    Currently wraps RipgrepSearch directly.
    Simple, no fallback logic needed.

    Usage:
        search = CodeSearch()
        result = await search.search("def.*retry", "/path/to/code")
        for match in result.matches:
            print(f"{match.file_path}:{match.line_number}")
    """

    def __init__(self):
        self.backend = RipgrepSearch()

    async def search(
        self,
        query: str,
        directory: str,
        max_results: int = 50,
        context_lines: int = 2,
        case_sensitive: bool = False,
    ) -> SearchResult:
        """
        Search for code patterns.

        Args:
            query: Regex pattern to search for
            directory: Directory to search in
            max_results: Maximum matches to return (default 50)
            context_lines: Lines of context before/after match (default 2)
            case_sensitive: Whether search is case-sensitive (default False)

        Returns:
            SearchResult with matches and metadata

        Example:
            result = await search.search("def main", ".", max_results=10)
            if result.success:
                print(f"Found {result.total_matches} matches")
        """
        return await self.backend.search(
            query, directory, max_results, context_lines, case_sensitive
        )

    async def is_available(self) -> bool:
        """Check if ripgrep is installed."""
        return await self.backend.is_available()
