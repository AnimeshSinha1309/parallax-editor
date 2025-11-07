"""
AI information feed widget for Parallax.
"""

from textual.widgets import Static, Label, Markdown
from textual.containers import Container, VerticalScroll
from textual.message import Message
from textual import events
from parallax.config.ai_config import get_ai_feed_config
from parallax.core.link_handler import LinkHandler


class InfoBox(Container):
    """
    A single information box with a header and content.
    """

    DEFAULT_CSS = """
    InfoBox {
        height: auto;
        padding: 1;
        margin-bottom: 1;
        border: solid $primary;
        background: $surface;
    }

    InfoBox.selected {
        border: heavy $accent;
        background: $boost;
    }

    InfoBox .info-header {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    InfoBox.selected .info-header {
        color: $secondary;
        text-style: bold;
    }

    InfoBox .info-content {
        color: $text;
        link-color: blue;
        link-style: underline;
    }

    InfoBox.selected .info-content {
        color: $text;
        link-color: blue;
        link-style: underline;
    }
    """

    def __init__(self, header: str, content: str, **kwargs):
        """
        Initialize an information box.

        Args:
            header: The header text
            content: The content text
            **kwargs: Additional keyword arguments for Container
        """
        super().__init__(**kwargs)
        self.header = header
        self.content = content

    def compose(self):
        """Compose the info box with header and content."""
        yield Label(self.header, classes="info-header")
        yield Markdown(self.content, classes="info-content")


class AIFeed(Container):
    """
    AI information feed widget that displays multiple information boxes.

    The content is configurable via the ai_config module.
    """

    DEFAULT_CSS = """
    AIFeed {
        width: 25%;
        height: 100%;
        background: $surface;
    }

    AIFeed VerticalScroll {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    """

    BINDINGS = [
        ("up,k", "navigate_up", "Move up"),
        ("down,j", "navigate_down", "Move down"),
    ]

    def __init__(self, root_path: str = ".", **kwargs):
        """
        Initialize the AI feed.

        Args:
            root_path: The root path for resolving relative file links
            **kwargs: Additional keyword arguments for Container
        """
        super().__init__(**kwargs)
        self.config = get_ai_feed_config()
        self.selected_index = 0
        self.can_focus = True
        self.root_path = root_path
        self.link_handler = LinkHandler(root_path=root_path)

    def compose(self):
        """Compose the AI feed with information boxes."""
        with VerticalScroll(id="ai-scroll"):
            for box_config in self.config:
                yield InfoBox(
                    header=box_config["header"],
                    content=box_config["content"]
                )

    def update_content(self, new_config: list[dict[str, str]]) -> None:
        """
        Update the AI feed with new content.

        Args:
            new_config: List of dictionaries with 'header' and 'content' keys
        """
        self.config = new_config

        # Remove existing boxes and add new ones
        scroll = self.query_one("#ai-scroll", VerticalScroll)
        scroll.remove_children()

        for box_config in self.config:
            scroll.mount(InfoBox(
                header=box_config["header"],
                content=box_config["content"]
            ))

    def add_info_box(self, header: str, content: str) -> None:
        """
        Add a new information box to the feed.

        Args:
            header: The header text
            content: The content text
        """
        scroll = self.query_one("#ai-scroll", VerticalScroll)
        scroll.mount(InfoBox(header=header, content=content))

    def remove_info_box(self, index: int) -> bool:
        """
        Remove an information box at the specified index.

        Args:
            index: The index of the box to remove

        Returns:
            bool: True if successful, False if index is out of range
        """
        scroll = self.query_one("#ai-scroll", VerticalScroll)
        children = list(scroll.children)

        if 0 <= index < len(children):
            children[index].remove()
            return True
        return False

    def get_box_count(self) -> int:
        """
        Get the number of information boxes in the feed.

        Returns:
            int: The number of boxes
        """
        scroll = self.query_one("#ai-scroll", VerticalScroll)
        return len(list(scroll.children))

    def _update_highlight(self) -> None:
        """Update the visual highlighting of the selected item."""
        scroll = self.query_one("#ai-scroll", VerticalScroll)
        children = list(scroll.children)

        # Remove selection from all boxes
        for child in children:
            if isinstance(child, InfoBox):
                child.remove_class("selected")

        # Add selection to current box
        if 0 <= self.selected_index < len(children):
            children[self.selected_index].add_class("selected")
            # Scroll to make sure the selected item is visible
            children[self.selected_index].scroll_visible()

    def action_navigate_up(self) -> None:
        """Navigate to the previous item in the feed."""
        if self.selected_index > 0:
            self.selected_index -= 1
            self._update_highlight()

    def action_navigate_down(self) -> None:
        """Navigate to the next item in the feed."""
        box_count = self.get_box_count()
        if self.selected_index < box_count - 1:
            self.selected_index += 1
            self._update_highlight()

    def delete_selected(self) -> tuple[bool, str, str]:
        """
        Delete the currently selected item.

        Returns:
            tuple: (success: bool, header: str, content: str)
        """
        scroll = self.query_one("#ai-scroll", VerticalScroll)
        children = list(scroll.children)

        if 0 <= self.selected_index < len(children):
            selected_box = children[self.selected_index]
            header = selected_box.header
            content = selected_box.content

            # Remove the box
            selected_box.remove()

            # Update config to stay in sync
            if 0 <= self.selected_index < len(self.config):
                self.config.pop(self.selected_index)

            # Update selected index
            new_count = self.get_box_count()
            if new_count == 0:
                self.selected_index = 0
            elif self.selected_index >= new_count:
                self.selected_index = new_count - 1

            # Update highlight
            self._update_highlight()

            return (True, header, content)

        return (False, "", "")

    def on_focus(self) -> None:
        """Handle focus event - highlight the selected item."""
        self._update_highlight()

    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        """
        Handle link clicks in markdown content.

        Args:
            event: The link clicked event containing the href
        """
        success, message = self.link_handler.handle_link(event.href)

        # You can optionally notify the user about the action
        if hasattr(self.app, 'notify'):
            if success:
                self.app.notify(message, severity="information")
            else:
                self.app.notify(message, severity="error")

    def get_selected_info(self) -> tuple[str, str] | None:
        """
        Get the header and content of the currently selected item.

        Returns:
            tuple: (header, content) or None if no valid selection
        """
        scroll = self.query_one("#ai-scroll", VerticalScroll)
        children = list(scroll.children)

        if 0 <= self.selected_index < len(children):
            box = children[self.selected_index]
            return (box.header, box.content)

        return None
