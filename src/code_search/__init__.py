"""Lightweight code search SDK using ripgrep."""

from .models import SearchMatch, SearchResult
from .search import CodeSearch

__all__ = ["CodeSearch", "SearchMatch", "SearchResult"]
__version__ = "0.1.0"
