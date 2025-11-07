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

        # TODO: Ghost text completion state
        self.ghost_text: Optional[str] = None
        self.ghost_text_visible: bool = False

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

    # =================================================================
    # TODO: Ghost Text Completion Methods - To be implemented
    # =================================================================
    #
    # Ghost text completions show inline suggestions as greyed-out text
    # at the cursor position. Users can accept with Tab or dismiss by
    # continuing to type.
    #
    # Implementation requirements:
    # 1. Extend TextArea or create custom rendering overlay
    # 2. Show completion text in grey after cursor position
    # 3. Handle Tab key to accept completion
    # 4. Clear ghost text on any other keystroke
    # 5. Respect cursor movement and clear if cursor moves
    #
    # Textual rendering approach options:
    # - Option A: Use Rich Text overlays with custom styling
    # - Option B: Extend TextArea's render method
    # - Option C: Use a separate overlay widget positioned at cursor
    #
    # =================================================================

    def set_ghost_text(self, completion: str) -> None:
        """
        Set the ghost text completion to display.

        TODO: Implement ghost text rendering in the editor.
        Currently just stores the text without displaying it.

        Args:
            completion: The completion text to show as ghost text
        """
        self.ghost_text = completion
        self.ghost_text_visible = True
        # TODO: Trigger render update to show ghost text at cursor position
        print(f"[TextEditor] Ghost text set: {completion[:50]}...")

    def clear_ghost_text(self) -> None:
        """
        Clear the current ghost text completion.

        TODO: Implement ghost text clearing in the editor.
        Currently just clears the internal state.
        """
        self.ghost_text = None
        self.ghost_text_visible = False
        # TODO: Trigger render update to remove ghost text

    def accept_ghost_text(self) -> bool:
        """
        Accept the ghost text completion and insert it at cursor position.

        TODO: Implement ghost text acceptance.
        Should insert the completion text at the current cursor position.

        Returns:
            bool: True if ghost text was accepted, False if no ghost text
        """
        if not self.ghost_text or not self.ghost_text_visible:
            return False

        try:
            text_area = self.query_one("#text-area", TextArea)
            cursor_row, cursor_col = text_area.cursor_location
            lines = text_area.text.split('\n')

            if cursor_row >= len(lines):
                return False

            # TODO: Insert ghost text at cursor position
            # For now, just clear it
            line = lines[cursor_row]
            new_line = line[:cursor_col] + self.ghost_text + line[cursor_col:]
            lines[cursor_row] = new_line

            text_area.load_text('\n'.join(lines))
            text_area.move_cursor((cursor_row, cursor_col + len(self.ghost_text)))

            self.clear_ghost_text()
            return True
        except Exception as e:
            print(f"[TextEditor] Error accepting ghost text: {e}")
            return False
