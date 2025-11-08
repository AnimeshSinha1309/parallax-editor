"""Tests for SearchResult Pydantic model serialization."""

import pytest
from utils.ripgrep import SearchResult, SearchMatch


def test_search_match_creation():
    """Test creating a SearchMatch."""
    match = SearchMatch(
        file_path="src/main.py",
        line_number=42,
        line_content="def main():",
        context_before=["import sys", ""],
        context_after=["    print('Hello')", ""]
    )

    assert match.file_path == "src/main.py"
    assert match.line_number == 42
    assert match.line_content == "def main():"
    assert len(match.context_before) == 2
    assert len(match.context_after) == 2
    assert str(match) == "src/main.py:42"


def test_search_result_creation():
    """Test creating a SearchResult."""
    match1 = SearchMatch(
        file_path="src/main.py",
        line_number=42,
        line_content="def main():",
        context_before=["import sys"],
        context_after=["    print('Hello')"]
    )

    match2 = SearchMatch(
        file_path="src/utils.py",
        line_number=10,
        line_content="def helper():",
        context_before=[],
        context_after=["    return True"]
    )

    result = SearchResult(
        matches=[match1, match2],
        total_matches=2,
        query="def.*\\(\\):",
        error=None
    )

    assert result.success is True
    assert result.total_matches == 2
    assert len(result.matches) == 2
    assert result.query == "def.*\\(\\):"


def test_search_result_with_error():
    """Test SearchResult with error."""
    result = SearchResult(
        matches=[],
        total_matches=0,
        query="invalid[",
        error="regex parse error"
    )

    assert result.success is False
    assert result.error == "regex parse error"
    assert len(result.matches) == 0


def test_search_result_json_serialization():
    """Test SearchResult JSON serialization and deserialization."""
    match = SearchMatch(
        file_path="src/test.py",
        line_number=15,
        line_content="    result = calculate(x, y)",
        context_before=["def process():", "    x = 10"],
        context_after=["    return result", ""]
    )

    original = SearchResult(
        matches=[match],
        total_matches=1,
        query="calculate",
        error=None
    )

    # Serialize to JSON
    json_str = original.to_json()
    assert isinstance(json_str, str)
    assert "src/test.py" in json_str
    assert "calculate" in json_str
    assert "15" in json_str

    # Deserialize from JSON
    deserialized = SearchResult.from_json(json_str)

    assert deserialized.total_matches == original.total_matches
    assert deserialized.query == original.query
    assert deserialized.error == original.error
    assert len(deserialized.matches) == len(original.matches)

    # Check match details
    orig_match = original.matches[0]
    deser_match = deserialized.matches[0]

    assert deser_match.file_path == orig_match.file_path
    assert deser_match.line_number == orig_match.line_number
    assert deser_match.line_content == orig_match.line_content
    assert deser_match.context_before == orig_match.context_before
    assert deser_match.context_after == orig_match.context_after


def test_search_result_formatted_string():
    """Test SearchResult formatted string output."""
    match1 = SearchMatch(
        file_path="src/main.py",
        line_number=42,
        line_content="def main():",
        context_before=["import sys", ""],
        context_after=["    print('Hello')", ""]
    )

    match2 = SearchMatch(
        file_path="src/utils.py",
        line_number=10,
        line_content="def helper():",
        context_before=[],
        context_after=["    return True"]
    )

    result = SearchResult(
        matches=[match1, match2],
        total_matches=2,
        query="def.*\\(\\):"
    )

    formatted = result.to_formatted_string()

    # Check that formatted string contains key information
    assert "Search Results for: def.*\\(\\):" in formatted
    assert "Total matches: 2" in formatted
    assert "src/main.py:42" in formatted
    assert "src/utils.py:10" in formatted
    assert "> def main():" in formatted
    assert "> def helper():" in formatted
    assert "import sys" in formatted
    assert "return True" in formatted


def test_search_result_formatted_string_no_matches():
    """Test formatted string when no matches."""
    result = SearchResult(
        matches=[],
        total_matches=0,
        query="nonexistent_function"
    )

    formatted = result.to_formatted_string()
    assert "No matches found for query: nonexistent_function" in formatted


def test_search_result_formatted_string_error():
    """Test formatted string when there's an error."""
    result = SearchResult(
        matches=[],
        total_matches=0,
        query="invalid[",
        error="regex parse error"
    )

    formatted = result.to_formatted_string()
    assert "Search Error: regex parse error" in formatted
    assert "Query: invalid[" in formatted


def test_search_result_empty_matches():
    """Test SearchResult with empty matches list."""
    result = SearchResult(
        matches=[],
        total_matches=0,
        query="test_query"
    )

    # Test JSON serialization with empty matches
    json_str = result.to_json()
    deserialized = SearchResult.from_json(json_str)

    assert deserialized.total_matches == 0
    assert len(deserialized.matches) == 0
    assert deserialized.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
