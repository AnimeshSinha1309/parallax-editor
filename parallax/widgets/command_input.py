"""
Command input widget for Parallax.
"""

from textual.widgets import Input
from textual.containers import Container
from textual.message import Message


class CommandInput(Container):
    """
    Command input widget for entering vim-style commands.

    Commands start with ':' and are executed when Enter is pressed.
    """

    DEFAULT_CSS = """
    CommandInput {
        height: 3;
        dock: bottom;
        border-top: solid $primary;
        background: $surface;
    }

    CommandInput Input {
        width: 100%;
        border: none;
    }
    """

    def __init__(self, **kwargs):
        """
        Initialize the command input.

        Args:
            **kwargs: Additional keyword arguments for Container
        """
        super().__init__(**kwargs)
        self.is_command_mode = False

    def compose(self):
        """Compose the command input with an Input widget."""
        yield Input(
            placeholder="Command mode - Type :help for available commands",
            id="command-input"
        )

    def on_mount(self) -> None:
        """Handle mount event."""
        input_widget = self.query_one("#command-input", Input)
        input_widget.display = True

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handle command submission.

        Args:
            event: The input submission event
        """
        command = event.value.strip()

        if command:
            # Post a message that the app can handle
            self.post_message(self.CommandSubmitted(command))

        # Clear the input and reset
        input_widget = self.query_one("#command-input", Input)
        input_widget.value = ""
        self.is_command_mode = False

    def on_key(self, event) -> None:
        """
        Handle key events to detect ':' for command mode.

        Args:
            event: The key event
        """
        input_widget = self.query_one("#command-input", Input)

        # If ':' is pressed and not in command mode, enter command mode
        if event.key == "colon" and not self.is_command_mode:
            self.is_command_mode = True
            input_widget.value = ":"
            input_widget.focus()
            event.prevent_default()
            event.stop()

    def focus_input(self) -> None:
        """Focus the command input."""
        input_widget = self.query_one("#command-input", Input)
        input_widget.focus()

    class CommandSubmitted(Message):
        """Message sent when a command is submitted."""

        def __init__(self, command: str) -> None:
            """
            Initialize the CommandSubmitted message.

            Args:
                command: The command string
            """
            super().__init__()
            self.command = command
