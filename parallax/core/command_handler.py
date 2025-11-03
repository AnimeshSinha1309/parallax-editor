"""
Command handler for processing vim-style commands in Parallax.
"""

from typing import Callable, Any


class CommandHandler:
    """
    Handles command parsing and execution for the Parallax editor.

    Commands are vim-style, starting with ':' prefix.
    This class provides a framework for registering and executing commands.
    """

    def __init__(self):
        """Initialize the command handler with an empty command registry."""
        self._commands: dict[str, Callable] = {}
        self._register_default_commands()

    def _register_default_commands(self):
        """Register default placeholder commands."""
        # These are placeholder methods that can be implemented later
        self.register_command("w", self._save)
        self.register_command("write", self._save)
        self.register_command("q", self._quit)
        self.register_command("quit", self._quit)
        self.register_command("wq", self._save_and_quit)
        self.register_command("open", self._open_file)

    def register_command(self, name: str, handler: Callable):
        """
        Register a command with its handler function.

        Args:
            name: The command name (without ':' prefix)
            handler: The function to call when command is executed
        """
        self._commands[name] = handler

    def execute(self, command_string: str) -> tuple[bool, str]:
        """
        Execute a command string.

        Args:
            command_string: The full command string (may include ':' prefix)

        Returns:
            tuple: (success: bool, message: str)
        """
        # Strip the leading ':' if present
        if command_string.startswith(':'):
            command_string = command_string[1:]

        # Parse command and arguments
        parts = command_string.strip().split(maxsplit=1)
        if not parts:
            return False, "Empty command"

        command_name = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        # Look up and execute command
        if command_name in self._commands:
            try:
                result = self._commands[command_name](args)
                return True, result or f"Executed: {command_name}"
            except Exception as e:
                return False, f"Error executing {command_name}: {str(e)}"
        else:
            return False, f"Unknown command: {command_name}"

    def get_registered_commands(self) -> list[str]:
        """
        Get a list of all registered command names.

        Returns:
            list: List of command names
        """
        return sorted(self._commands.keys())

    # Placeholder command implementations
    # These should be overridden or properly implemented when integrating with the app

    def _save(self, args: str) -> str:
        """Placeholder for save command."""
        return f"Save command called with args: {args}" if args else "Save command called"

    def _quit(self, args: str) -> str:
        """Placeholder for quit command."""
        return "Quit command called"

    def _save_and_quit(self, args: str) -> str:
        """Placeholder for save and quit command."""
        return "Save and quit command called"

    def _open_file(self, args: str) -> str:
        """Placeholder for open file command."""
        if not args:
            return "Error: No filename specified"
        return f"Open file command called with: {args}"
