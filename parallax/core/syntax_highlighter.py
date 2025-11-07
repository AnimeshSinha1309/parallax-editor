"""
Syntax highlighter for the Parallax text editor.
"""

import re
from typing import Optional


class SyntaxHighlighter:
    """
    Provides syntax highlighting for various file types.

    Currently supports Markdown with an extensible architecture
    for adding more languages.
    """

    # Supported file extensions
    MARKDOWN_EXTENSIONS = {'.md', '.markdown', '.mdown', '.mkd'}

    def __init__(self):
        """Initialize the syntax highlighter."""
        self._highlighters = {
            'markdown': self._highlight_markdown,
            'plain': self._highlight_plain,
        }

    def detect_language(self, filename: Optional[str]) -> str:
        """
        Detect the language/syntax type based on file extension.

        Args:
            filename: The name of the file (optional)

        Returns:
            str: The detected language type ('markdown', 'plain', etc.)
        """
        if not filename:
            return 'plain'

        # Get file extension
        ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

        if ext in self.MARKDOWN_EXTENSIONS:
            return 'markdown'

        # Default to plain text
        return 'plain'

    def highlight(self, content: str, language: Optional[str] = None, filename: Optional[str] = None) -> str:
        """
        Apply syntax highlighting to content.

        Args:
            content: The text content to highlight
            language: The language to use (optional, auto-detected if None)
            filename: The filename to help detect language (optional)

        Returns:
            str: The content with Textual/Rich markup for syntax highlighting
        """
        if language is None:
            language = self.detect_language(filename)

        highlighter = self._highlighters.get(language, self._highlight_plain)
        return highlighter(content)

    def _highlight_plain(self, content: str) -> str:
        """
        Return plain text without highlighting.

        Args:
            content: The text content

        Returns:
            str: The same content without markup
        """
        return content

    def _highlight_markdown(self, content: str) -> str:
        """
        Apply Markdown syntax highlighting using Rich markup.

        This is a basic implementation. For production use, consider
        using Rich's built-in Markdown highlighter or Pygments.

        Args:
            content: The Markdown content

        Returns:
            str: Content with Rich markup tags
        """
        # This is a simplified version. In practice, you'd use Rich's
        # Markdown class or Pygments for more comprehensive highlighting.

        # For now, we'll return the content as-is and rely on Textual's
        # TextArea widget which has built-in syntax highlighting support
        # when we specify the language parameter.

        return content

    def add_language(self, language: str, highlighter_func: callable):
        """
        Add support for a new language.

        Args:
            language: The language identifier (e.g., 'python', 'javascript')
            highlighter_func: A function that takes content and returns highlighted content
        """
        self._highlighters[language] = highlighter_func

    def get_supported_languages(self) -> list[str]:
        """
        Get a list of supported languages.

        Returns:
            list: List of language identifiers
        """
        return list(self._highlighters.keys())
