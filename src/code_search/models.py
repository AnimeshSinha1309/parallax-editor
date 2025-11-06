"""Data models for code search results."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SearchMatch:
    """A single match from code search."""

    file_path: str  # Path to file (relative to search dir)
    line_number: int  # Line number (1-indexed)
    line_content: str  # The matching line content
    context_before: List[str] = field(default_factory=list)  # Lines before match
    context_after: List[str] = field(default_factory=list)  # Lines after match

    def __str__(self) -> str:
        """Format as file:line for display."""
        return f"{self.file_path}:{self.line_number}"


@dataclass
class SearchResult:
    """Complete search result."""

    matches: List[SearchMatch]
    total_matches: int
    query: str
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """True if search completed without errors."""
        return self.error is None
