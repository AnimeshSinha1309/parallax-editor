"""Lightweight code search SDK using ripgrep."""

from ..models import Card
from utils.codesearch.models import SearchMatch, SearchResult
from .search import CodeSearch
from utils.codesearch.context import RipgrepContext, RipgrepContextError

__all__ = [
    "CodeSearch",
    "SearchMatch",
    "SearchResult",
    "RipgrepContext",
    "RipgrepContextError",
    "Card",
]
__version__ = "0.1.0"
