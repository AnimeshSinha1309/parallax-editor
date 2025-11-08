"""
Main application for Parallax text editor.
"""

import logging
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, TextArea
from parallax.widgets.file_explorer import FileExplorer
from parallax.widgets.text_editor import TextEditor
from parallax.widgets.ai_feed import AIFeed
from parallax.widgets.command_input import CommandInput
from parallax.core.command_handler import CommandHandler
from parallax.core.feed_handler import FeedHandler
from parallax.core.logging_config import setup_logging, get_logger
from fulfillers import Card, CardType
from fulfillers.completions import Completions
from fulfillers.ambiguities import Ambiguities
from fulfillers.web_context import WebContext
from utils.context import GlobalPreferenceContext
from textual import events

logger = get_logger("parallax.app")


class ParallaxApp(App):
    """
    Parallax - A modern terminal text editor with AI assistance.

    Features a 3-pane layout:
    - Left: File explorer
    - Center: Text editor
    - Right: AI information feed
    - Bottom: Command mode
    """

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        width: 100%;
        height: 100%;
    }

    #panes {
        width: 100%;
        height: 1fr;
    }
    """

    BINDINGS = [
        ("escape", "exit_to_command", "Command mode"),
    ]

    def __init__(self, global_context: GlobalPreferenceContext = None, **kwargs):
        """
        Initialize the Parallax application.

        Args:
            global_context: Global preference context containing scope root and plan path
            **kwargs: Additional keyword arguments for App
        """
        # Set up logging before anything else
        setup_logging(log_level="INFO")

        # Use default context if none provided
        if global_context is None:
            global_context = GlobalPreferenceContext(scope_root=".", plan_path=None)

        logger.info(f"Initializing Parallax application with scope_root={global_context.scope_root}, plan_path={global_context.plan_path}")

        super().__init__(**kwargs)
        self.global_context = global_context
        self.root_path = global_context.scope_root  # For backwards compatibility with widgets
        self.command_handler = CommandHandler()
        self.yankboard = ""  # For yank/paste operations
        self.feed_handler = FeedHandler(threshold=20, global_context=global_context)  # Trigger every 20 characters
        logger.debug("FeedHandler initialized")

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()

        with Container(id="main-container"):
            with Horizontal(id="panes"):
                yield FileExplorer(root_path=self.root_path, id="file-explorer")
                yield TextEditor(id="text-editor")
                yield AIFeed(root_path=self.root_path, id="ai-feed")

            yield CommandInput(id="command-input")

        yield Footer()

    def on_mount(self) -> None:
        """Handle mount event."""
        logger.info("ParallaxApp mounted, setting up components")
        self.title = "Parallax"
        self.sub_title = "Terminal Text Editor"

        # Set up feed handler with AI feed and text editor
        ai_feed = self.query_one("#ai-feed", AIFeed)
        self.feed_handler.set_ai_feed(ai_feed)
        logger.debug("AI feed connected to FeedHandler")

        text_editor = self.query_one("#text-editor", TextEditor)
        self.feed_handler.set_text_editor(text_editor)
        logger.debug("TextEditor connected to FeedHandler")

        # Register fulfillers
        logger.info("Registering fulfillers...")

        # Register Ambiguities fulfiller
        try:
            ambiguities_fulfiller = Ambiguities()
            self.feed_handler.register_fulfiller(ambiguities_fulfiller)
            logger.info("Ambiguities fulfiller registered successfully")
        except Exception as e:
            logger.warning(f"Failed to register Ambiguities fulfiller: {e}")

        # Register WebContext fulfiller
        try:
            web_context_fulfiller = WebContext()
            self.feed_handler.register_fulfiller(web_context_fulfiller)
            logger.info("WebContext fulfiller registered successfully")
        except Exception as e:
            logger.warning(f"Failed to register WebContext fulfiller: {e}")

        # Register Completions fulfiller
        try:
            completions_fulfiller = Completions()
            self.feed_handler.register_fulfiller(completions_fulfiller)
            logger.info("Completions fulfiller registered successfully")
        except Exception as e:
            logger.warning(f"Failed to register Completions fulfiller: {e}")

        # Start in command mode by default
        command_input = self.query_one("#command-input", CommandInput)
        command_input.focus_input()
        logger.info("Parallax startup complete")

    def on_file_explorer_file_selected(self, message: FileExplorer.FileSelected) -> None:
        """
        Handle file selection from the file explorer.

        Args:
            message: The file selection message containing the file path
        """
        if message.path.is_file():
            editor = self.query_one("#text-editor", TextEditor)
            editor.load_file(message.path)

    def on_command_input_command_submitted(self, message: CommandInput.CommandSubmitted) -> None:
        """
        Handle command submission from the command input.

        Args:
            message: The command submission message
        """
        cmd = message.command.strip()

        # Handle commands
        if cmd in [":q", ":quit"]:
            self.exit()
        elif cmd in [":w", ":write"]:
            editor = self.query_one("#text-editor", TextEditor)
            if editor.save_file():
                self.notify("File saved successfully", severity="information")
            else:
                self.notify("No file to save", severity="warning")
        elif cmd in [":wq"]:
            editor = self.query_one("#text-editor", TextEditor)
            if editor.save_file():
                self.exit()
            else:
                self.notify("Could not save file", severity="error")
        elif cmd == ":edit":
            # Enter edit mode
            text_area = self.query_one("#text-area", TextArea)
            text_area.focus()
            self.notify("Edit mode - Press Escape to return", severity="information")
        elif cmd == ":files":
            # Enter files mode
            tree = self.query_one("#directory-tree")
            tree.focus()
            self.notify("Files mode - Press Escape to return", severity="information")
        elif cmd == ":feed":
            # Enter feed mode
            feed = self.query_one("#ai-feed", AIFeed)
            feed.focus()
            self.notify("Feed mode - Use j/k or arrows to navigate, :dd to delete - Press Escape to return", severity="information")
        elif cmd == ":help":
            help_text = """Available Commands:
Navigation:
  :edit     - Enter edit mode
  :files    - Enter file explorer mode
  :feed     - Enter AI feed mode (navigate with j/k or arrows)
  :gg       - Go to top of file
  :G        - Go to bottom of file
  :<N>      - Go to line N (e.g., :42)

Editing (must be in edit mode):
  :dd       - Delete current line (in edit mode) or AI suggestion (in feed mode)
  :dw       - Delete word under cursor
  :x        - Delete character under cursor
  :yy       - Yank (copy) current line
  :p        - Paste yanked content below

File Operations:
  :w        - Save current file
  :q        - Quit Parallax
  :wq       - Save and quit
  :help     - Show this help"""
            self.notify(help_text, severity="information", timeout=15)
        elif cmd == ":dd":
            # Delete line or AI suggestion depending on context
            focused = self.focused
            if focused and focused.id == "ai-feed":
                # In feed mode - delete AI suggestion
                feed = self.query_one("#ai-feed", AIFeed)
                success, header, content = feed.delete_selected()
                if success:
                    # Mark this suggestion as deleted
                    self.feed_handler.mark_suggestion_deleted(header, content)
                    # Sync feed_handler's feed_items with the AI feed
                    # Note: feed_items are already Card objects in FeedHandler
                    self.notify(f"Deleted suggestion: {header}", severity="information")
                else:
                    self.notify("Failed to delete suggestion", severity="error")
            else:
                # In edit mode - delete line
                editor = self.query_one("#text-editor", TextEditor)
                if editor.delete_line():
                    self.notify("Line deleted", severity="information")
                else:
                    self.notify("Failed to delete line", severity="error")
        elif cmd == ":dw":
            # Delete word
            editor = self.query_one("#text-editor", TextEditor)
            if editor.delete_word():
                self.notify("Word deleted", severity="information")
            else:
                self.notify("Failed to delete word", severity="error")
        elif cmd == ":x":
            # Delete character
            editor = self.query_one("#text-editor", TextEditor)
            if editor.delete_char():
                self.notify("Character deleted", severity="information")
            else:
                self.notify("Failed to delete character", severity="error")
        elif cmd == ":yy":
            # Yank line
            editor = self.query_one("#text-editor", TextEditor)
            yanked = editor.yank_line()
            if yanked is not None:
                self.yankboard = yanked
                self.notify("Line yanked", severity="information")
            else:
                self.notify("Failed to yank line", severity="error")
        elif cmd == ":p":
            # Paste
            if self.yankboard:
                editor = self.query_one("#text-editor", TextEditor)
                if editor.paste_line(self.clipboard):
                    self.notify("Content pasted", severity="information")
                else:
                    self.notify("Failed to paste", severity="error")
            else:
                self.notify("Nothing to paste", severity="warning")
        elif cmd == ":gg":
            # Go to top
            editor = self.query_one("#text-editor", TextEditor)
            if editor.go_to_top():
                self.notify("Moved to top", severity="information")
        elif cmd == ":G":
            # Go to bottom
            editor = self.query_one("#text-editor", TextEditor)
            if editor.go_to_bottom():
                self.notify("Moved to bottom", severity="information")
        elif cmd.startswith(":") and cmd[1:].isdigit():
            # Go to line number (e.g., :42)
            line_num = int(cmd[1:])
            editor = self.query_one("#text-editor", TextEditor)
            if editor.go_to_line(line_num):
                self.notify(f"Moved to line {line_num}", severity="information")
        else:
            # Unknown command
            self.notify(f"Unknown command: {cmd}. Type :help for available commands.", severity="error")

    def action_exit_to_command(self) -> None:
        """Exit current mode and return to command mode."""
        command_input = self.query_one("#command-input", CommandInput)
        command_input.focus_input()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """
        Handle text area content changes.

        Args:
            event: The TextArea.Changed event
        """
        # Only track changes in the main text editor
        if event.text_area.id == "text-area":
            logger.debug("Text area changed event received")
            # Get cursor position from text area
            cursor_pos = event.text_area.cursor_location
            logger.debug(f"Notifying FeedHandler of text change at cursor {cursor_pos}")
            # Pass text and cursor position to feed handler
            self.feed_handler.on_text_change(event.text_area.text, cursor_pos)

    def on_key(self, event: events.Key) -> None:
        """
        Handle keyboard events for ghost text completion.

        Args:
            event: The keyboard event
        """
        # Only handle ghost text keys when in edit mode (text area has focus)
        focused = self.focused
        if not focused or focused.id != "text-area":
            return

        editor = self.query_one("#text-editor", TextEditor)
        self.feed_handler.reset_completion_flag()
