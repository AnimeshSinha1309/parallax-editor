"""Unit tests for code search SDK."""

import pytest
import os
import sys

# Add fulfillers and utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fulfillers"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from codesearch import CodeSearch, SearchMatch, SearchResult
from utils.ripgrep import RipgrepSearch

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.mark.asyncio
async def test_ripgrep_available():
    """Test that ripgrep is installed"""
    rg = RipgrepSearch()
    assert await rg.is_available(), "ripgrep not installed"


@pytest.mark.asyncio
async def test_basic_search():
    """Test basic search functionality"""
    search = CodeSearch()

    result = await search.search(query="retry", directory=FIXTURES_DIR, max_results=10)

    assert result.success, f"Search failed: {result.error}"
    assert result.total_matches > 0, "No matches found"
    assert result.query == "retry"

    # Check match structure
    match = result.matches[0]
    assert hasattr(match, "file_path")
    assert hasattr(match, "line_number")
    assert hasattr(match, "line_content")
    assert "retry" in match.line_content.lower()


@pytest.mark.asyncio
async def test_case_sensitive():
    """Test case-sensitive search"""
    search = CodeSearch()

    # Case-insensitive (default)
    result_insensitive = await search.search(
        query="RETRY", directory=FIXTURES_DIR, case_sensitive=False
    )

    # Case-sensitive
    result_sensitive = await search.search(
        query="RETRY", directory=FIXTURES_DIR, case_sensitive=True
    )

    # Insensitive should find matches, sensitive should not
    assert result_insensitive.total_matches > 0
    assert result_sensitive.total_matches == 0


@pytest.mark.asyncio
async def test_context_lines():
    """Test that context lines are captured"""
    search = CodeSearch()

    result = await search.search(
        query="def retry_request", directory=FIXTURES_DIR, context_lines=2
    )

    assert result.success
    assert len(result.matches) > 0

    match = result.matches[0]
    # Should have context lines (at least one of before or after)
    assert len(match.context_before) > 0 or len(match.context_after) > 0


@pytest.mark.asyncio
async def test_max_results():
    """Test that max_results is respected"""
    search = CodeSearch()

    result = await search.search(
        query="retry", directory=FIXTURES_DIR, max_results=3
    )

    assert result.success
    # Total should not exceed max_results
    assert result.total_matches <= 3


@pytest.mark.asyncio
async def test_nonexistent_directory():
    """Test search in nonexistent directory"""
    search = CodeSearch()

    result = await search.search(query="test", directory="/nonexistent/path/12345")

    # Should return error, not crash
    assert not result.success
    assert result.error is not None


@pytest.mark.asyncio
async def test_invalid_regex():
    """Test search with invalid regex"""
    search = CodeSearch()

    result = await search.search(query="[invalid(", directory=FIXTURES_DIR)

    # Should handle gracefully
    assert not result.success
    assert result.error is not None


@pytest.mark.asyncio
async def test_search_match_str():
    """Test SearchMatch string formatting"""
    match = SearchMatch(
        file_path="test.py", line_number=42, line_content="def test():"
    )
    assert str(match) == "test.py:42"


@pytest.mark.asyncio
async def test_search_result_success_property():
    """Test SearchResult success property"""
    # Success case
    result_ok = SearchResult(matches=[], total_matches=0, query="test")
    assert result_ok.success

    # Error case
    result_err = SearchResult(
        matches=[], total_matches=0, query="test", error="Something went wrong"
    )
    assert not result_err.success


@pytest.mark.asyncio
async def test_multiple_files():
    """Test that search finds matches across multiple files"""
    search = CodeSearch()

    result = await search.search(query="retry", directory=FIXTURES_DIR, max_results=20)

    assert result.success
    assert result.total_matches > 0

    # Should have matches from different files
    file_paths = {match.file_path for match in result.matches}
    assert len(file_paths) > 1, "Should find matches in multiple files"


@pytest.mark.asyncio
async def test_regex_pattern():
    """Test regex pattern matching"""
    search = CodeSearch()

    # Search for function definitions with 'retry' in name
    result = await search.search(
        query=r"(def|function|public).*retry", directory=FIXTURES_DIR
    )

    assert result.success
    assert result.total_matches > 0

    # All matches should contain 'retry'
    for match in result.matches:
        assert "retry" in match.line_content.lower()


@pytest.mark.asyncio
async def test_context_before_and_after():
    """Test that both before and after context are captured"""
    search = CodeSearch()

    # Search for a function definition that has code before and after
    result = await search.search(
        query="def retry_request", directory=FIXTURES_DIR, context_lines=3
    )

    assert result.success
    assert len(result.matches) > 0

    match = result.matches[0]
    # The function definition should have imports before it
    assert len(match.context_before) > 0
    # And should have the function body after it
    assert len(match.context_after) > 0
