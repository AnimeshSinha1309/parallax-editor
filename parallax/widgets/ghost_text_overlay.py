"""
Ghost text overlay widget for inline completions.
"""

from textual.widgets import Static, TextArea
from textual.reactive import reactive


class GhostTextOverlay(Static):
    """
    An overlay widget that displays ghost text (inline completion suggestions)
    at the cursor position in grey/dim styling.

    The ghost text appears inline and can be accepted with Tab or Right arrow,
    or dismissed with Escape or by continuing to type.
    """

    ghost_text = reactive("", init=False)

    DEFAULT_CSS = """
    GhostTextOverlay {
        width: 1fr;
        height: 1fr;
        background: transparent;
        color: $text-muted;
        text-opacity: 50%;
        layer: overlay;
    }
    """

    def __init__(self, text_area: TextArea, **kwargs):
        """
        Initialize the ghost text overlay.

        Args:
            text_area: The TextArea to overlay on
            **kwargs: Additional keyword arguments for Static
        """
        super().__init__(**kwargs)
        self.text_area = text_area
        self.can_focus = False  # Don't steal focus from TextArea

    def watch_ghost_text(self, new_text: str) -> None:
        """Watch for changes to ghost_text and trigger re-render."""
        self.update(new_text)

    def render(self) -> str:
        """
        Render the ghost text at the cursor position.

        Returns:
            The ghost text string to display
        """
        if not self.ghost_text or not self.text_area:
            return ""

        try:
            # Get cursor position
            cursor_row, cursor_col = self.text_area.cursor_location

            # Get the text content
            lines = self.text_area.text.split('\n')

            # Build the display with ghost text positioned at cursor
            # We'll create padding to position the ghost text correctly
            result_lines = []

            for i, line in enumerate(lines):
                if i == cursor_row:
                    # This is the cursor line - add ghost text after cursor position
                    # We need to pad with spaces to reach cursor column
                    padding = " " * cursor_col
                    ghost_line = padding + self.ghost_text
                    result_lines.append(ghost_line)
                else:
                    # Empty line for other rows
                    result_lines.append("")

            return "\n".join(result_lines)

        except Exception as e:
            # If anything goes wrong, just don't show ghost text
            return ""

    def set_ghost_text(self, text: str) -> None:
        """
        Set the ghost text to display.

        Args:
            text: The completion text to show
        """
        self.ghost_text = text
        self.refresh()

    def clear_ghost_text(self) -> None:
        """Clear the ghost text."""
        self.ghost_text = ""
        self.refresh()
