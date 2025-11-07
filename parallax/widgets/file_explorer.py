"""
File explorer widget for Parallax.
"""

from pathlib import Path
from textual.widgets import DirectoryTree
from textual.containers import Container
from textual.message import Message


class FileExplorer(Container):
    """
    A file explorer widget that displays the directory tree structure.

    Uses Textual's DirectoryTree for navigation.
    """

    DEFAULT_CSS = """
    FileExplorer {
        width: 25%;
        border-right: solid $primary;
    }

    FileExplorer DirectoryTree {
        width: 100%;
        height: 100%;
        background: $surface;
    }
    """

    def __init__(self, root_path: str = ".", **kwargs):
        """
        Initialize the file explorer.

        Args:
            root_path: The root directory to display (defaults to current directory)
            **kwargs: Additional keyword arguments for Container
        """
        super().__init__(**kwargs)
        self.root_path = Path(root_path).resolve()

    def compose(self):
        """Compose the file explorer with a DirectoryTree widget."""
        yield DirectoryTree(str(self.root_path), id="directory-tree")

    def on_mount(self) -> None:
        """Handle mount event."""
        tree = self.query_one("#directory-tree", DirectoryTree)
        tree.show_root = True
        tree.guide_depth = 4

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """
        Handle file selection event.

        Args:
            event: The file selection event containing the selected file path

        This method is called when a file is selected in the directory tree.
        It posts a custom message that the main app can listen to.
        """
        # Post a message that can be caught by the parent app
        self.post_message(self.FileSelected(event.path))

    class FileSelected(Message):
        """Message sent when a file is selected."""

        def __init__(self, path: Path) -> None:
            """
            Initialize the FileSelected message.

            Args:
                path: The path to the selected file
            """
            super().__init__()
            self.path = path
