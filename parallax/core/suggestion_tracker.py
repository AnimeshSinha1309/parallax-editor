"""
Suggestion tracker for managing deleted AI suggestions.
"""

import json
from pathlib import Path
from typing import Set


class SuggestionTracker:
    """
    Tracks deleted AI suggestions to avoid re-surfacing them.
    """

    def __init__(self, storage_file: str = ".parallax_deleted_suggestions.json"):
        """
        Initialize the suggestion tracker.

        Args:
            storage_file: Path to the file storing deleted suggestions
        """
        self.storage_file = Path.home() / storage_file
        self.deleted_suggestions: Set[str] = set()
        self._load()

    def _load(self) -> None:
        """Load deleted suggestions from storage file."""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    self.deleted_suggestions = set(data.get("deleted", []))
            except (json.JSONDecodeError, IOError):
                # If file is corrupted or can't be read, start fresh
                self.deleted_suggestions = set()

    def _save(self) -> None:
        """Save deleted suggestions to storage file."""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump({"deleted": list(self.deleted_suggestions)}, f, indent=2)
        except IOError:
            # Silently fail if we can't write (e.g., permission issues)
            pass

    def mark_deleted(self, header: str, content: str) -> None:
        """
        Mark a suggestion as deleted.

        Args:
            header: The header of the suggestion
            content: The content of the suggestion
        """
        # Create a unique key from header and content
        key = self._make_key(header, content)
        self.deleted_suggestions.add(key)
        self._save()

    def is_deleted(self, header: str, content: str) -> bool:
        """
        Check if a suggestion has been deleted.

        Args:
            header: The header of the suggestion
            content: The content of the suggestion

        Returns:
            bool: True if the suggestion was deleted
        """
        key = self._make_key(header, content)
        return key in self.deleted_suggestions

    def _make_key(self, header: str, content: str) -> str:
        """
        Create a unique key for a suggestion.

        Args:
            header: The header text
            content: The content text

        Returns:
            str: A unique key for the suggestion
        """
        # Simple concatenation with separator
        return f"{header}|||{content}"

    def clear_all(self) -> None:
        """Clear all deleted suggestions."""
        self.deleted_suggestions.clear()
        self._save()

    def get_deleted_count(self) -> int:
        """
        Get the number of deleted suggestions.

        Returns:
            int: Number of deleted suggestions
        """
        return len(self.deleted_suggestions)
