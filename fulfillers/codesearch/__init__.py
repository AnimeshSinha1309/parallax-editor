"""Lightweight code search SDK using ripgrep."""

from ..models import Card
from utils.ripgrep import SearchMatch, SearchResult
from .search import CodeSearch
from utils.context import PreferenceContext, PreferenceContextError

__all__ = [
    "CodeSearch",
    "SearchMatch",
    "SearchResult",
    "PreferenceContext",
    "PreferenceContextError",
    "Card",
]
__version__ = "0.1.0"
