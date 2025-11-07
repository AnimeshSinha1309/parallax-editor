"""
Text editor widget for Parallax.
"""

from pathlib import Path
from typing import Optional
from textual.widgets import TextArea
from textual.containers import Container
from parallax.core.syntax_highlighter import SyntaxHighlighter


class TextEditor(Container):
    """
    A text editor widget with syntax highlighting and line numbers.

    Built on top of Textual's TextArea widget.
    """

    DEFAULT_CSS = """
    TextEditor {
        width: 50%;
        border-right: solid $primary;
    }

    TextEditor TextArea {
        width: 100%;
        height: 100%;
    }
    """

    def __init__(self, **kwargs):
        """
        Initialize the text editor.

        Args:
            **kwargs: Additional keyword arguments for Container
        """
        super().__init__(**kwargs)
        self.syntax_highlighter = SyntaxHighlighter()
        self.current_file: Optional[Path] = None
        self.current_language: str = "plain"

    def compose(self):
        """Compose the text editor with a TextArea widget."""
        text_area = TextArea(
            id="text-area",
            show_line_numbers=True,
            theme="monokai",
        )
        # Don't auto-focus - let the app control focus
        yield text_area

    def load_file(self, file_path: Path) -> None:
        """
        Load a file into the editor.

        Args:
            file_path: Path to the file to load
        """
        try:
            self.current_file = file_path
            content = file_path.read_text()

            # Detect language for syntax highlighting
            self.current_language = self.syntax_highlighter.detect_language(file_path.name)

            # Update the text area
            text_area = self.query_one("#text-area", TextArea)

            # Set the language for Textual's built-in syntax highlighting
            # Textual supports: python, markdown, json, yaml, toml, sql, etc.
            if self.current_language == "markdown":
                text_area.language = "markdown"
            else:
                text_area.language = None

            text_area.load_text(content)

        except Exception as e:
            # Handle file loading errors
            text_area = self.query_one("#text-area", TextArea)
            text_area.load_text(f"Error loading file: {str(e)}")

    def get_content(self) -> str:
        """
        Get the current content of the editor.

        Returns:
            str: The current text content
        """
        text_area = self.query_one("#text-area", TextArea)
        return text_area.text

    def set_content(self, content: str) -> None:
        """
        Set the content of the editor.

        Args:
            content: The text content to set
        """
        text_area = self.query_one("#text-area", TextArea)
        text_area.load_text(content)

    def save_file(self) -> bool:
        """
        Save the current content to the file.

        Returns:
            bool: True if save was successful, False otherwise
        """
        if not self.current_file:
            return False

        try:
            content = self.get_content()
            self.current_file.write_text(content)
            return True
        except Exception:
            return False

    def clear(self) -> None:
        """Clear the editor content."""
        text_area = self.query_one("#text-area", TextArea)
        text_area.clear()
        self.current_file = None
        self.current_language = "plain"

    def delete_line(self) -> bool:
        """
        Delete the current line (vim's dd motion).

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            text_area = self.query_one("#text-area", TextArea)
            cursor_row, _ = text_area.cursor_location
            lines = text_area.text.split('\n')

            if 0 <= cursor_row < len(lines):
                lines.pop(cursor_row)
                text_area.load_text('\n'.join(lines))
                # Keep cursor on same line (or last line if we deleted the last one)
                new_row = min(cursor_row, len(lines) - 1) if lines else 0
                text_area.move_cursor((new_row, 0))
                return True
            return False
        except Exception:
            return False

    def delete_word(self) -> bool:
        """
        Delete the word under/after cursor (vim's dw motion).

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            text_area = self.query_one("#text-area", TextArea)
            cursor_row, cursor_col = text_area.cursor_location
            lines = text_area.text.split('\n')

            if cursor_row >= len(lines):
                return False

            line = lines[cursor_row]
            if cursor_col >= len(line):
                return False

            # Find the end of the current word
            end = cursor_col
            # Skip non-whitespace
            while end < len(line) and not line[end].isspace():
                end += 1
            # Skip trailing whitespace
            while end < len(line) and line[end].isspace():
                end += 1

            # Delete from cursor to end of word
            new_line = line[:cursor_col] + line[end:]
            lines[cursor_row] = new_line
            text_area.load_text('\n'.join(lines))
            text_area.move_cursor((cursor_row, cursor_col))
            return True
        except Exception:
            return False

    def yank_line(self) -> Optional[str]:
        """
        Yank (copy) the current line (vim's yy motion).

        Returns:
            Optional[str]: The yanked line, or None if unsuccessful
        """
        try:
            text_area = self.query_one("#text-area", TextArea)
            cursor_row, _ = text_area.cursor_location
            lines = text_area.text.split('\n')

            if 0 <= cursor_row < len(lines):
                return lines[cursor_row]
            return None
        except Exception:
            return None

    def paste_line(self, content: str) -> bool:
        """
        Paste content below the current line (vim's p motion).

        Args:
            content: The content to paste

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            text_area = self.query_one("#text-area", TextArea)
            cursor_row, _ = text_area.cursor_location
            lines = text_area.text.split('\n')

            # Insert below current line
            lines.insert(cursor_row + 1, content)
            text_area.load_text('\n'.join(lines))
            text_area.move_cursor((cursor_row + 1, 0))
            return True
        except Exception:
            return False

    def go_to_line(self, line_number: int) -> bool:
        """
        Go to a specific line number.

        Args:
            line_number: The line number to go to (1-indexed)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            text_area = self.query_one("#text-area", TextArea)
            lines = text_area.text.split('\n')

            # Convert to 0-indexed and clamp to valid range
            target_row = max(0, min(line_number - 1, len(lines) - 1))
            text_area.move_cursor((target_row, 0))
            return True
        except Exception:
            return False

    def go_to_top(self) -> bool:
        """
        Go to the top of the file (vim's gg motion).

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            text_area = self.query_one("#text-area", TextArea)
            text_area.move_cursor((0, 0))
            return True
        except Exception:
            return False

    def go_to_bottom(self) -> bool:
        """
        Go to the bottom of the file (vim's G motion).

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            text_area = self.query_one("#text-area", TextArea)
            lines = text_area.text.split('\n')
            last_row = max(0, len(lines) - 1)
            text_area.move_cursor((last_row, 0))
            return True
        except Exception:
            return False

    def delete_char(self) -> bool:
        """
        Delete the character under the cursor (vim's x motion).

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            text_area = self.query_one("#text-area", TextArea)
            cursor_row, cursor_col = text_area.cursor_location
            lines = text_area.text.split('\n')

            if cursor_row >= len(lines):
                return False

            line = lines[cursor_row]
            if cursor_col >= len(line):
                return False

            # Delete character at cursor
            new_line = line[:cursor_col] + line[cursor_col + 1:]
            lines[cursor_row] = new_line
            text_area.load_text('\n'.join(lines))
            text_area.move_cursor((cursor_row, cursor_col))
            return True
        except Exception:
            return False
