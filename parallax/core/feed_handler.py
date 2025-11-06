"""
Feed handler for dynamic updates based on editor activity.
"""

import random
from typing import Optional
from textual.widgets import TextArea
from parallax.core.suggestion_tracker import SuggestionTracker


class FeedHandler:
    """
    Handles dynamic updates to the AI feed based on editor activity.

    Tracks character changes and triggers updates after a specified threshold.
    """

    def __init__(self, threshold: int = 20):
        """
        Initialize the feed handler.

        Args:
            threshold: Number of characters to type before triggering an update
        """
        self.threshold = threshold
        self.char_count = 0
        self.last_content = ""
        self.ai_feed = None
        self.feed_items: list[dict[str, str]] = []
        self.suggestion_tracker = SuggestionTracker()

    def set_ai_feed(self, ai_feed) -> None:
        """
        Set the AI feed widget to update.

        Args:
            ai_feed: The AIFeed widget instance
        """
        self.ai_feed = ai_feed
        # Initialize with current feed items
        self.feed_items = list(ai_feed.config)

    def on_text_change(self, new_content: str) -> None:
        """
        Handle text change in the editor.

        Args:
            new_content: The new content of the editor
        """
        # Calculate the difference in character count
        char_diff = abs(len(new_content) - len(self.last_content))
        self.char_count += char_diff
        self.last_content = new_content

        # Check if we've reached the threshold
        if self.char_count >= self.threshold:
            self._trigger_update()
            self.char_count = 0  # Reset counter

    def _trigger_update(self) -> None:
        """
        Trigger an update to the AI feed.

        Deletes an arbitrary old item and adds a new item at a different location.
        """
        if self.ai_feed is None:
            return

        # Delete an arbitrary old item (if there are items to delete)
        if len(self.feed_items) > 0:
            # Pick a random item to delete
            delete_index = random.randint(0, len(self.feed_items) - 1)
            deleted_item = self.feed_items.pop(delete_index)
            print(f"[FeedHandler] Deleted item at index {delete_index}: {deleted_item['header']}")

        # Add a new item at a random position
        new_item = self._generate_new_item()

        # Insert at a random position (or at the end if feed is empty)
        if len(self.feed_items) > 0:
            insert_index = random.randint(0, len(self.feed_items))
        else:
            insert_index = 0

        self.feed_items.insert(insert_index, new_item)
        print(f"[FeedHandler] Added new item at index {insert_index}: {new_item['header']}")

        # Update the AI feed widget
        self.ai_feed.update_content(self.feed_items)

    def _generate_new_item(self) -> dict[str, str]:
        """
        Generate a new feed item.

        Returns:
            dict: A dictionary with 'header' and 'content' keys
        """
        # For now, generate simple placeholder content
        # In the future, this could be replaced with LLM-generated suggestions
        all_suggestions = [
            {
                "header": "Code Suggestion",
                "content": "Consider adding type hints to improve code clarity and catch type-related bugs early."
            },
            {
                "header": "Refactoring Tip",
                "content": "This function is getting long. Consider breaking it into smaller, more focused functions."
            },
            {
                "header": "Best Practice",
                "content": "Add docstrings to your functions to improve code documentation and maintainability."
            },
            {
                "header": "Performance Tip",
                "content": "Consider using list comprehensions instead of loops for better performance and readability."
            },
            {
                "header": "Style Guide",
                "content": "Follow PEP 8 conventions for consistent code formatting across your project."
            },
            {
                "header": "Testing Reminder",
                "content": "Don't forget to write unit tests for this new functionality!"
            },
            {
                "header": "Security Note",
                "content": "Be cautious with user input. Always validate and sanitize data before processing."
            },
            {
                "header": "Code Review",
                "content": "Review your error handling. Ensure all edge cases are covered appropriately."
            },
        ]

        # Filter out deleted suggestions
        available_suggestions = [
            s for s in all_suggestions
            if not self.suggestion_tracker.is_deleted(s["header"], s["content"])
        ]

        # If all suggestions are deleted, return a fallback
        if not available_suggestions:
            return {
                "header": "AI Assistant",
                "content": "Keep coding! You're doing great."
            }

        return random.choice(available_suggestions)

    def push_item(self, header: str, content: str, position: Optional[int] = None) -> None:
        """
        Manually push a new item to the feed.

        Args:
            header: The header text for the new item
            content: The content text for the new item
            position: Optional position to insert at (default: end of feed)
        """
        new_item = {"header": header, "content": content}

        if position is None or position >= len(self.feed_items):
            self.feed_items.append(new_item)
        else:
            self.feed_items.insert(position, new_item)

        if self.ai_feed:
            self.ai_feed.update_content(self.feed_items)

    def delete_item(self, index: int) -> bool:
        """
        Delete an item from the feed at the specified index.

        Args:
            index: The index of the item to delete

        Returns:
            bool: True if successful, False if index is out of range
        """
        if 0 <= index < len(self.feed_items):
            self.feed_items.pop(index)
            if self.ai_feed:
                self.ai_feed.update_content(self.feed_items)
            return True
        return False

    def reset_counter(self) -> None:
        """Reset the character counter."""
        self.char_count = 0

    def get_counter(self) -> int:
        """
        Get the current character counter value.

        Returns:
            int: Current character count
        """
        return self.char_count

    def mark_suggestion_deleted(self, header: str, content: str) -> None:
        """
        Mark a suggestion as deleted to avoid re-surfacing it.

        Args:
            header: The header of the deleted suggestion
            content: The content of the deleted suggestion
        """
        self.suggestion_tracker.mark_deleted(header, content)
