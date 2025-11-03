"""
Unit tests for the CommandHandler class.
"""

import pytest
from parallax.core.command_handler import CommandHandler


class TestCommandHandler:
    """Test suite for CommandHandler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = CommandHandler()

    def test_initialization(self):
        """Test that CommandHandler initializes correctly."""
        assert self.handler is not None
        assert isinstance(self.handler._commands, dict)
        assert len(self.handler._commands) > 0

    def test_default_commands_registered(self):
        """Test that default commands are registered."""
        commands = self.handler.get_registered_commands()
        assert "w" in commands
        assert "write" in commands
        assert "q" in commands
        assert "quit" in commands
        assert "wq" in commands
        assert "open" in commands

    def test_execute_with_colon_prefix(self):
        """Test executing a command with ':' prefix."""
        success, message = self.handler.execute(":w")
        assert success is True
        assert "Save" in message or "Executed" in message

    def test_execute_without_colon_prefix(self):
        """Test executing a command without ':' prefix."""
        success, message = self.handler.execute("w")
        assert success is True
        assert "Save" in message or "Executed" in message

    def test_execute_unknown_command(self):
        """Test executing an unknown command."""
        success, message = self.handler.execute(":unknown")
        assert success is False
        assert "Unknown command" in message

    def test_execute_empty_command(self):
        """Test executing an empty command."""
        success, message = self.handler.execute(":")
        assert success is False
        assert "Empty command" in message

    def test_execute_command_with_args(self):
        """Test executing a command with arguments."""
        success, message = self.handler.execute(":open test.txt")
        assert success is True
        assert "test.txt" in message

    def test_register_custom_command(self):
        """Test registering a custom command."""
        def custom_handler(args):
            return f"Custom: {args}"

        self.handler.register_command("custom", custom_handler)
        commands = self.handler.get_registered_commands()
        assert "custom" in commands

        success, message = self.handler.execute(":custom arg")
        assert success is True
        assert "Custom: arg" in message

    def test_get_registered_commands(self):
        """Test getting list of registered commands."""
        commands = self.handler.get_registered_commands()
        assert isinstance(commands, list)
        assert len(commands) > 0
        assert all(isinstance(cmd, str) for cmd in commands)

    def test_command_error_handling(self):
        """Test that command errors are handled gracefully."""
        def error_handler(args):
            raise ValueError("Test error")

        self.handler.register_command("error", error_handler)
        success, message = self.handler.execute(":error")
        assert success is False
        assert "Error executing" in message

    def test_save_command(self):
        """Test save command execution."""
        success, message = self.handler.execute(":w")
        assert success is True

    def test_quit_command(self):
        """Test quit command execution."""
        success, message = self.handler.execute(":q")
        assert success is True

    def test_save_and_quit_command(self):
        """Test save and quit command execution."""
        success, message = self.handler.execute(":wq")
        assert success is True

    def test_open_without_filename(self):
        """Test open command without filename."""
        success, message = self.handler.execute(":open")
        assert success is True
        assert "No filename" in message

    def test_command_case_sensitivity(self):
        """Test that commands are case-sensitive."""
        success1, _ = self.handler.execute(":w")
        success2, _ = self.handler.execute(":W")
        assert success1 is True
        assert success2 is False
