"""
Feed handler for dynamic updates based on editor activity.
"""

import asyncio
import random
from typing import Optional, List, Tuple
from textual.widgets import TextArea
from parallax.core.suggestion_tracker import SuggestionTracker
from fulfillers import Fulfiller, Card, CardType


class FeedHandler:
    """
    Handles dynamic updates to the AI feed based on editor activity.

    Tracks character changes and triggers updates after a specified threshold.
    Uses registered fulfillers to generate cards asynchronously.
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
        self.cursor_position: Tuple[int, int] = (0, 0)
        self.ai_feed = None
        self.text_editor = None  # TODO: Set via set_text_editor() for ghost text
        self.feed_items: List[Card] = []
        self.suggestion_tracker = SuggestionTracker()
        self.fulfillers: List[Fulfiller] = []
        self._update_in_progress = False

    def register_fulfiller(self, fulfiller: Fulfiller) -> None:
        """
        Register a fulfiller to be invoked during updates.

        Args:
            fulfiller: A Fulfiller instance to register
        """
        self.fulfillers.append(fulfiller)

    def set_ai_feed(self, ai_feed) -> None:
        """
        Set the AI feed widget to update.

        Args:
            ai_feed: The AIFeed widget instance
        """
        self.ai_feed = ai_feed
        # Initialize with current feed items (convert from old format if needed)
        if hasattr(ai_feed, 'config') and ai_feed.config:
            # Convert old dict format to Card objects if necessary
            for item in ai_feed.config:
                if isinstance(item, dict):
                    # Legacy format conversion - assume CONTEXT type
                    card = Card(
                        header=item.get("header", ""),
                        text=item.get("content", ""),
                        type=CardType.CONTEXT,
                        metadata={"source": "legacy"}
                    )
                    self.feed_items.append(card)
                elif isinstance(item, Card):
                    self.feed_items.append(item)

    def set_text_editor(self, text_editor) -> None:
        """
        Set the text editor widget for ghost text completions.

        TODO: This is needed for ghost text implementation.
        Currently stores the reference but ghost text rendering is not yet implemented.

        Args:
            text_editor: The TextEditor widget instance
        """
        self.text_editor = text_editor

    def update_cursor_position(self, position: Tuple[int, int]) -> None:
        """
        Update the current cursor position.

        Args:
            position: (row, col) tuple of cursor position
        """
        self.cursor_position = position

    def on_text_change(self, new_content: str, cursor_position: Optional[Tuple[int, int]] = None) -> None:
        """
        Handle text change in the editor.

        Args:
            new_content: The new content of the editor
            cursor_position: Optional cursor position (row, col)
        """
        # Update cursor position if provided
        if cursor_position is not None:
            self.cursor_position = cursor_position

        # Calculate the difference in character count
        char_diff = abs(len(new_content) - len(self.last_content))
        self.char_count += char_diff
        self.last_content = new_content

        # Check if we've reached the threshold
        if self.char_count >= self.threshold:
            # Trigger async update (schedule as task)
            asyncio.create_task(self._trigger_update_async(new_content))
            self.char_count = 0  # Reset counter

    async def _trigger_update_async(self, text_buffer: str) -> None:
        """
        Trigger an async update to the AI feed and ghost text.

        Invokes all registered fulfillers concurrently and processes their results.

        Args:
            text_buffer: The current text buffer content
        """
        if self._update_in_progress:
            print("[FeedHandler] Update already in progress, skipping...")
            return

        if not self.fulfillers:
            print("[FeedHandler] No fulfillers registered, skipping update")
            return

        self._update_in_progress = True

        try:
            # Invoke all fulfillers concurrently
            tasks = [
                fulfiller.invoke(
                    text_buffer=text_buffer,
                    cursor_position=self.cursor_position,
                    query_intent="editor_update"
                )
                for fulfiller in self.fulfillers
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Flatten all cards from all fulfillers
            all_cards: List[Card] = []
            for result in results:
                if isinstance(result, Exception):
                    print(f"[FeedHandler] Fulfiller error: {result}")
                    continue
                if isinstance(result, list):
                    all_cards.extend(result)

            # Separate cards by type
            completion_cards = [c for c in all_cards if c.type == CardType.COMPLETION]
            feed_cards = [c for c in all_cards if c.type in (CardType.QUESTION, CardType.CONTEXT)]

            # Handle ghost text completions
            if completion_cards:
                print(f"[FeedHandler] Received {len(completion_cards)} completion cards for ghost text")
                # TODO: Implement ghost text rendering in the editor
                # For now, just call set_ghost_text if editor is available
                if self.text_editor:
                    # Use the first completion card
                    completion_text = completion_cards[0].text
                    self.text_editor.set_ghost_text(completion_text)
                    print(f"[FeedHandler] Set ghost text: {completion_text[:50]}...")
                else:
                    print(f"[FeedHandler] TODO: TextEditor not set, cannot render ghost text")

            # Handle feed cards - update the sidebar
            if feed_cards:
                # Delete an arbitrary old item (if there are items to delete)
                if len(self.feed_items) > 0:
                    delete_index = random.randint(0, len(self.feed_items) - 1)
                    deleted_item = self.feed_items.pop(delete_index)
                    print(f"[FeedHandler] Deleted item at index {delete_index}: {deleted_item.header}")

                # Add new cards at random positions
                for card in feed_cards:
                    if len(self.feed_items) > 0:
                        insert_index = random.randint(0, len(self.feed_items))
                    else:
                        insert_index = 0

                    self.feed_items.insert(insert_index, card)
                    print(f"[FeedHandler] Added new item at index {insert_index}: {card.header}")

                # Update the AI feed widget
                if self.ai_feed:
                    self.ai_feed.update_content(self.feed_items)

        except Exception as e:
            print(f"[FeedHandler] Error during update: {e}")
        finally:
            self._update_in_progress = False

    def push_card(self, card: Card, position: Optional[int] = None) -> None:
        """
        Manually push a new card to the feed.

        Args:
            card: The Card object to add
            position: Optional position to insert at (default: end of feed)
        """
        if position is None or position >= len(self.feed_items):
            self.feed_items.append(card)
        else:
            self.feed_items.insert(position, card)

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
