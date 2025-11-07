"""Data models for fulfiller responses."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class Card:
    """
    A card represents a single result or piece of information from a fulfiller.

    Cards are the standard output format for all fulfillers and are displayed
    to the user in the UI.
    """

    header: str  # Title or header text for the card
    text: str  # Main content text
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

    # Future extensions can be added here:
    # icon: Optional[str] = None
    # actions: List[Action] = field(default_factory=list)
    # priority: int = 0
    # etc.

    def __str__(self) -> str:
        """Format card as string for display."""
        return f"{self.header}: {self.text[:50]}..."
