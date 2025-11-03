"""
AI information feed widget for Parallax.
"""

from textual.widgets import Static, Label
from textual.containers import Container, VerticalScroll
from parallax.config.ai_config import get_ai_feed_config


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

    InfoBox .info-header {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    InfoBox .info-content {
        color: $text;
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
        yield Static(self.content, classes="info-content")


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

    def __init__(self, **kwargs):
        """
        Initialize the AI feed.

        Args:
            **kwargs: Additional keyword arguments for Container
        """
        super().__init__(**kwargs)
        self.config = get_ai_feed_config()

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
