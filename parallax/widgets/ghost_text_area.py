"""
Custom TextArea with ghost text support.
"""

from typing import Optional
import logging
from textual.widgets import TextArea
from rich.text import Text

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
        self.ghost_text_visible: bool = False
        # Store the actual text separately to preserve it
        self._actual_text = ""
        self._ghost_applied = False

    def set_ghost_text(self, completion: str) -> None:
        """
        Set the ghost text completion to display.

        Args:
            completion: The completion text to show as ghost text
        """
        logger.debug(f"GhostTextArea.set_ghost_text called: {completion[:50] if completion else 'None'}...")
        if not completion:
            self.clear_ghost_text()
            return

        self.ghost_text = completion
        self.ghost_text_visible = True
        self._apply_ghost_text()
        logger.info("Ghost text applied to TextArea")

    def clear_ghost_text(self) -> None:
        """Clear the ghost text and restore original content."""
        logger.debug("GhostTextArea.clear_ghost_text called")
        if not self.ghost_text_visible:
            logger.debug("No ghost text visible, nothing to clear")
            return

        self.ghost_text = None
        self.ghost_text_visible = False

        if self._ghost_applied:
            logger.debug("Clearing applied ghost text")
            # Remove ghost text by restoring actual text
            self._ghost_applied = False
            # Restore cursor position
            cursor_pos = self.cursor_location
            # Just refresh to remove visual ghost text
            self.refresh()
            logger.info("Ghost text cleared from TextArea")

    def accept_ghost_text(self) -> bool:
        """
        Accept the ghost text and insert it into the document.

        Returns:
            bool: True if ghost text was accepted, False otherwise
        """
        logger.info("GhostTextArea.accept_ghost_text called")
        if not self.ghost_text or not self.ghost_text_visible:
            logger.debug("No ghost text to accept")
            return False

        try:
            # Get current state
            cursor_row, cursor_col = self.cursor_location
            completion = self.ghost_text
            logger.debug(f"Accepting ghost text at ({cursor_row}, {cursor_col}): {completion[:50]}...")

            # Clear ghost text first
            self.ghost_text = None
            self.ghost_text_visible = False
            self._ghost_applied = False

            # Insert the completion text at cursor
            lines = self.text.split('\n')
            if cursor_row < len(lines):
                line = lines[cursor_row]
                new_line = line[:cursor_col] + completion + line[cursor_col:]
                lines[cursor_row] = new_line

                # Update text
                self.load_text('\n'.join(lines))

                # Move cursor to end of inserted text
                new_cursor_col = cursor_col + len(completion)
                self.move_cursor((cursor_row, new_cursor_col))
                logger.info(f"Ghost text inserted, cursor moved to ({cursor_row}, {new_cursor_col})")

            return True

        except Exception as e:
            logger.error(f"Error accepting ghost text: {e}", exc_info=True)
            return False

    def _apply_ghost_text(self) -> None:
        """Apply ghost text visualization."""
        if not self.ghost_text or not self.ghost_text_visible:
            return

        try:
            # Mark that we've applied ghost text
            self._ghost_applied = True

            # For now, just store that we have ghost text
            # The actual rendering will happen in the render method
            # This is a simplified approach - full implementation would
            # require overriding TextArea's rendering pipeline

            # As a simple visual indicator, we'll just refresh
            self.refresh()

        except Exception as e:
            print(f"[GhostTextArea] Error applying ghost text: {e}")

    def on_key(self, event) -> None:
        """Handle key events to manage ghost text."""
        # Clear ghost text on most keystrokes (except Tab, Right, Escape which are handled in ParallaxApp)
        if self.ghost_text_visible and event.key not in ["tab", "right", "escape"]:
            logger.debug(f"Key '{event.key}' pressed, clearing ghost text")
            self.clear_ghost_text()
        # Event will bubble up naturally in Textual's event system
        # No need to call super() - TextArea doesn't have on_key method
