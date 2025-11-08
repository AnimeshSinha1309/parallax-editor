"""
Custom TextArea with ghost text support.
"""

from typing import Optional
import logging
from textual.widgets import TextArea
from rich.text import Text
import copy

logger = logging.getLogger("parallax.ghost_text_area")


class GhostTextArea(TextArea):
    """
    Extended TextArea that supports inline ghost text completions.

    Ghost text appears as dimmed/grey text at the cursor position and can be
    accepted with Tab/Right arrow or dismissed with Escape.
    """

    def __init__(self, *args, **kwargs):
        """Initialize GhostTextArea with ghost text support."""
        super().__init__(*args, **kwargs)
        self.ghost_text: Optional[str] = None
        self.ghost_text_start_position: Optional[tuple[int, int]] = None
        self.ghost_text_end_position: Optional[tuple[int, int]] = None

    def set_ghost_text(self, completion: str) -> None:
        """
        Set the ghost text completion to display.

        Args:
            completion: The completion text to show as ghost text
        """
        logger.info(f"GhostTextArea.set_ghost_text called: {completion[:50] if completion else 'None'}...")
        if completion != self.ghost_text:
            self.clear_ghost_text()
            self.ghost_text = completion
        
        self.ghost_text_start_position = copy.copy(self.cursor_location)
        self.insert(self.ghost_text)
        self.ghost_text_end_position = copy.copy(self.cursor_location)
        # self.get_text_range(self.ghost_text_start_position, self.ghost_text_end_position).style = "dim"
        self.move_cursor(self.ghost_text_start_position)

    def clear_ghost_text(self) -> None:
        """Clear the ghost text and restore original content."""
        logger.info("GhostTextArea.clear_ghost_text called")
        if self.ghost_text_start_position is None or self.ghost_text_end_position is None:
            return

        # self.delete(self.ghost_text_start_position, self.ghost_text_end_position)
        # self.ghost_text = None
        # self.ghost_text_end_position = None
        # self.ghost_text_start_position = None

    def accept_ghost_text(self) -> bool:
        """
        Accept the ghost text and insert it into the document.

        Returns:
            bool: True if ghost text was accepted, False otherwise
        """
        logger.info("GhostTextArea.accept_ghost_text called")
        ghost_text_copy = copy.copy(self.ghost_text)
        self.clear_ghost_text()
        self.insert(ghost_text_copy)
        return True

    def _on_key(self, event) -> None:
        """Handle key events to manage ghost text."""
        # Clear ghost text on most keystrokes (except Tab, Right, Escape which are handled in ParallaxApp)
        # if self.ghost_text is not None and event.key not in ["tab", "right", "escape"]:
            # logger.debug(f"Key '{event.key}' pressed, clearing ghost text")
            # self.clear_ghost_text()
        return super()._on_key(event)
