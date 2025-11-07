"""
Unit tests for the SyntaxHighlighter class.
"""

import pytest
from parallax.core.syntax_highlighter import SyntaxHighlighter


class TestSyntaxHighlighter:
    """Test suite for SyntaxHighlighter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.highlighter = SyntaxHighlighter()

    def test_initialization(self):
        """Test that SyntaxHighlighter initializes correctly."""
        assert self.highlighter is not None
        assert hasattr(self.highlighter, '_highlighters')
        assert isinstance(self.highlighter._highlighters, dict)

    def test_detect_language_markdown(self):
        """Test detection of Markdown files."""
        assert self.highlighter.detect_language("test.md") == "markdown"
        assert self.highlighter.detect_language("README.markdown") == "markdown"
        assert self.highlighter.detect_language("doc.mdown") == "markdown"
        assert self.highlighter.detect_language("file.mkd") == "markdown"

    def test_detect_language_plain(self):
        """Test detection of plain text files."""
        assert self.highlighter.detect_language("test.txt") == "plain"
        assert self.highlighter.detect_language("file.log") == "plain"
        assert self.highlighter.detect_language("random.xyz") == "plain"

    def test_detect_language_no_extension(self):
        """Test detection when file has no extension."""
        assert self.highlighter.detect_language("README") == "plain"
        assert self.highlighter.detect_language("Makefile") == "plain"

    def test_detect_language_none(self):
        """Test detection when filename is None."""
        assert self.highlighter.detect_language(None) == "plain"

    def test_detect_language_case_insensitive(self):
        """Test that language detection is case-insensitive."""
        assert self.highlighter.detect_language("test.MD") == "markdown"
        assert self.highlighter.detect_language("test.Md") == "markdown"
        assert self.highlighter.detect_language("test.MARKDOWN") == "markdown"

    def test_highlight_plain_text(self):
        """Test highlighting plain text."""
        content = "This is plain text"
        result = self.highlighter.highlight(content, language="plain")
        assert result == content

    def test_highlight_markdown(self):
        """Test highlighting Markdown content."""
        content = "# Header\n\nThis is **bold** text"
        result = self.highlighter.highlight(content, language="markdown")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_highlight_auto_detect(self):
        """Test automatic language detection during highlighting."""
        content = "# Markdown Header"
        result = self.highlighter.highlight(content, filename="test.md")
        assert isinstance(result, str)

    def test_highlight_with_explicit_language(self):
        """Test highlighting with explicitly specified language."""
        content = "Some content"
        result = self.highlighter.highlight(content, language="markdown")
        assert isinstance(result, str)

    def test_add_language(self):
        """Test adding a new language highlighter."""
        def custom_highlighter(content):
            return f"CUSTOM: {content}"

        self.highlighter.add_language("custom", custom_highlighter)
        languages = self.highlighter.get_supported_languages()
        assert "custom" in languages

        result = self.highlighter.highlight("test", language="custom")
        assert result == "CUSTOM: test"

    def test_get_supported_languages(self):
        """Test getting list of supported languages."""
        languages = self.highlighter.get_supported_languages()
        assert isinstance(languages, list)
        assert "markdown" in languages
        assert "plain" in languages

    def test_highlight_empty_content(self):
        """Test highlighting empty content."""
        result = self.highlighter.highlight("")
        assert result == ""

    def test_highlight_multiline_content(self):
        """Test highlighting multiline content."""
        content = "Line 1\nLine 2\nLine 3"
        result = self.highlighter.highlight(content, language="plain")
        assert result == content
        assert "\n" in result

    def test_markdown_extensions(self):
        """Test that MARKDOWN_EXTENSIONS is properly defined."""
        assert hasattr(SyntaxHighlighter, 'MARKDOWN_EXTENSIONS')
        assert isinstance(SyntaxHighlighter.MARKDOWN_EXTENSIONS, set)
        assert '.md' in SyntaxHighlighter.MARKDOWN_EXTENSIONS

    def test_highlight_unknown_language_fallback(self):
        """Test that unknown languages fall back to plain text."""
        content = "test content"
        result = self.highlighter.highlight(content, language="unknown_language")
        assert result == content
