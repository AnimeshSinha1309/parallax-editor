"""
Feed handler for dynamic updates based on editor activity.
"""

import asyncio
import random
import logging
import os
from typing import Optional, List, Tuple, Dict, Any
from textual.widgets import TextArea
import httpx
from parallax.core.suggestion_tracker import SuggestionTracker
from shared.models import Card, CardType
from shared.context import GlobalPreferenceContext

logger = logging.getLogger("parallax.feed_handler")

# Backend server configuration
PARALLIZER_URL = os.getenv("PARALLIZER_URL", "http://localhost:8000")


class FeedHandler:
    """
    Handles dynamic updates to the AI feed based on editor activity.

    Tracks character changes and triggers updates after a specified threshold.
    Uses registered fulfillers to generate cards asynchronously.
    """

    def __init__(self, threshold: int = 20, global_context: GlobalPreferenceContext = None, idle_timeout: float = 4.0, user_id: str = "default_user"):
        """
        Initialize the feed handler.

        Args:
            threshold: Number of characters to type before triggering an update
            global_context: Global preference context containing scope root and plan path
            idle_timeout: Time in seconds to wait after last keystroke before triggering completion
            user_id: User identifier for backend session management
        """
        # Use default context if none provided
        if global_context is None:
            global_context = GlobalPreferenceContext(scope_root=".", plan_path=None)

        logger.info(f"Initializing FeedHandler with threshold={threshold}, scope_root={global_context.scope_root}, plan_path={global_context.plan_path}, idle_timeout={idle_timeout}s, user_id={user_id}")
        logger.info(f"Backend server URL: {PARALLIZER_URL}")
        self.threshold = threshold
        self.idle_timeout = idle_timeout
        self.char_count = 0
        self.last_content = ""
        self.cursor_position: Tuple[int, int] = (0, 0)
        self.global_context = global_context
        self.user_id = user_id
        self.ai_feed = None
        self.text_editor = None
        self.feed_items: List[Card] = []
        self.suggestion_tracker = SuggestionTracker()
        self._update_in_progress = False
        self._last_completion_triggered = False
        self._idle_task: Optional[asyncio.Task] = None
        self._ignoring_next_change = False
        self._last_successful_cards: List[Card] = []  # Cache last successful response for retry
        self._http_client = httpx.AsyncClient(timeout=30.0)
        self._polling_task: Optional[asyncio.Task] = None  # Background polling task
        self._stop_polling = False  # Flag to stop polling

    def register_fulfiller(self, fulfiller) -> None:
        """
        Legacy method for fulfiller registration (now handled by backend).

        This method is kept for backward compatibility but does nothing,
        as fulfillers are now managed by the Parallizer backend server.

        Args:
            fulfiller: A Fulfiller instance (ignored)
        """
        fulfiller_name = fulfiller.__class__.__name__ if hasattr(fulfiller, '__class__') else str(fulfiller)
        logger.info(f"Ignoring fulfiller registration for '{fulfiller_name}' - fulfillers are now managed by backend")

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

    def reset_completion_flag(self) -> None:
        """Reset the completion triggered flag, allowing new completions to be requested."""
        logger.debug("Resetting completion flag - new completions can be triggered")
        self._last_completion_triggered = False

    def mark_ghost_text_change(self) -> None:
        """Mark that the next text change is from ghost text and should be ignored."""
        self._ignoring_next_change = True
        logger.debug("Marked next change to be ignored (ghost text change)")

    def on_text_change(self, new_content: str, cursor_position: Optional[Tuple[int, int]] = None, from_ghost_text: bool = False) -> None:
        """
        Handle text change in the editor.

        Args:
            new_content: The new content of the editor
            cursor_position: Optional cursor position (row, col)
            from_ghost_text: If True, this change is from ghost text and should be ignored
        """
        # Update cursor position if provided
        if cursor_position is not None:
            self.cursor_position = cursor_position

        # Ignore changes from ghost text application/removal
        if from_ghost_text or self._ignoring_next_change:
            logger.debug("Ignoring text change from ghost text")
            self._ignoring_next_change = False
            self.last_content = new_content
            return

        # User made a change - reset completion flag to allow new completions
        if self._last_completion_triggered:
            logger.debug("User typed after completion was triggered, resetting completion flag")
            self._last_completion_triggered = False

        # Cancel any pending idle timer
        if self._idle_task and not self._idle_task.done():
            logger.debug("Canceling pending idle timer")
            self._idle_task.cancel()

        # Calculate the difference in character count
        char_diff = abs(len(new_content) - len(self.last_content))
        self.char_count += char_diff
        self.last_content = new_content

        logger.debug(f"Text changed: char_count={self.char_count}/{self.threshold}, cursor={self.cursor_position}")

        # Check if we've reached the threshold
        if self.char_count >= self.threshold and not self._last_completion_triggered:
            logger.debug(f"Threshold reached ({self.char_count} >= {self.threshold})")

            # Start idle timer to trigger backend request
            logger.debug(f"Starting {self.idle_timeout}s idle timer for backend request")
            self._idle_task = asyncio.create_task(self._wait_and_trigger_idle(new_content))
        elif self._last_completion_triggered:
            logger.debug("Completion already triggered, not starting new timer")

    async def _wait_and_trigger_idle(self, document_text: str) -> None:
        """
        Wait for idle timeout, then trigger all fulfillers if still idle.

        Args:
            document_text: The current document text content
        """
        try:
            logger.debug(f"Waiting {self.idle_timeout}s for idle timeout...")
            await asyncio.sleep(self.idle_timeout)
            logger.info("Idle timeout elapsed, triggering fulfillers")
            await self._trigger_update_async(document_text)
            # Reset counter after successful trigger
            self.char_count = 0
        except asyncio.CancelledError:
            logger.debug("Idle timer cancelled (user continued typing)")
            # Don't reset counter - keep accumulating

    async def _call_backend(self, document_text: str) -> Optional[List[Card]]:
        """
        Call the Parallizer backend to get cards.

        Triggers background processing and starts polling if needed.

        Args:
            document_text: The current document text content

        Returns:
            List of Card objects, or None if the request failed
        """
        try:
            logger.info(f"Calling backend at {PARALLIZER_URL}/fulfill")

            # Prepare request payload
            payload = {
                "user_id": self.user_id,
                "document_text": document_text,
                "cursor_position": list(self.cursor_position),
                "global_context": {
                    "scope_root": self.global_context.scope_root,
                    "plan_path": self.global_context.plan_path
                }
            }

            # Make HTTP request with timeout
            response = await self._http_client.post(
                f"{PARALLIZER_URL}/fulfill",
                json=payload,
                timeout=10.0  # 10 second timeout for initial response
            )

            if response.status_code == 200:
                data = response.json()
                processing = data.get("processing", False)

                cards = []
                # Convert JSON response to Card objects
                for card_data in data.get("cards", []):
                    card = Card(
                        header=card_data["header"],
                        text=card_data["text"],
                        type=CardType(card_data["type"]),
                        metadata=card_data.get("metadata", {})
                    )
                    cards.append(card)

                logger.info(f"Backend returned {len(cards)} cards (processing={processing})")

                # Start polling if backend is still processing
                if processing:
                    logger.info("Backend is processing in background, starting polling...")
                    self._start_polling()

                return cards
            else:
                logger.error(f"Backend request failed with status {response.status_code}: {response.text}")
                return None

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.warning(f"Backend request timed out or failed to connect: {e}")
            # Start polling to get cached results
            logger.info("Starting polling to get cached results...")
            self._start_polling()
            return None
        except Exception as e:
            logger.error(f"Error calling backend: {e}", exc_info=True)
            return None

    def _start_polling(self):
        """Start polling the /cached endpoint for updates"""
        # Cancel existing polling task if any
        if self._polling_task and not self._polling_task.done():
            logger.debug("Cancelling existing polling task")
            self._polling_task.cancel()

        # Start new polling task
        self._stop_polling = False
        self._polling_task = asyncio.create_task(self._poll_cached())
        logger.info("Started polling task")

    async def _poll_cached(self):
        """
        Poll the /cached endpoint every 3 seconds for incremental updates.
        Continues until backend signals processing is complete.
        """
        logger.info(f"Starting to poll cached endpoint for user {self.user_id}")
        poll_count = 0

        try:
            while not self._stop_polling:
                try:
                    poll_count += 1
                    logger.debug(f"Polling cached endpoint (attempt {poll_count})...")

                    # Request cached data
                    response = await self._http_client.get(
                        f"{PARALLIZER_URL}/cached/{self.user_id}",
                        timeout=5.0
                    )

                    if response.status_code == 200:
                        data = response.json()
                        processing = data.get("processing", False)
                        last_updated = data.get("last_updated", 0)

                        # Convert cards
                        cards = []
                        for card_data in data.get("cards", []):
                            card = Card(
                                header=card_data["header"],
                                text=card_data["text"],
                                type=CardType(card_data["type"]),
                                metadata=card_data.get("metadata", {})
                            )
                            cards.append(card)

                        logger.debug(f"Cached endpoint returned {len(cards)} cards (processing={processing})")

                        # Always update UI with cards from server (replaces entire feed)
                        # This ensures UI stays in sync with server's cache
                        self._update_ui_with_cards(cards)

                        # Stop polling if backend finished processing
                        if not processing:
                            logger.info("Backend finished processing, stopping polling")
                            break

                    else:
                        logger.warning(f"Cached request failed with status {response.status_code}")

                except asyncio.CancelledError:
                    logger.debug("Polling task cancelled")
                    raise
                except Exception as e:
                    logger.error(f"Error in polling iteration: {e}")

                # Wait 3 seconds before next poll
                await asyncio.sleep(3.0)

        except asyncio.CancelledError:
            logger.info("Polling cancelled")
        finally:
            logger.info(f"Stopped polling after {poll_count} attempts")

    def _update_ui_with_cards(self, cards: List[Card]):
        """
        Update UI with new cards from backend.
        Replaces current feed_items and updates widgets.
        """
        # Replace feed items
        self.feed_items = cards

        # Separate by type
        completion_cards = [c for c in cards if c.type == CardType.COMPLETION]
        feed_cards = [c for c in cards if c.type in (CardType.QUESTION, CardType.CONTEXT, CardType.MATH, CardType.EMAIL)]

        # Update ghost text if we have completions
        if completion_cards and self.text_editor:
            completion_text = completion_cards[0].text
            logger.debug(f"Updating ghost text: {completion_text[:50]}...")
            self.text_editor.set_ghost_text(completion_text)
            self._last_completion_triggered = True

        # Always update AI feed with current feed cards (may be empty to clear the feed)
        if self.ai_feed:
            logger.debug(f"Updating AI feed with {len(feed_cards)} cards")
            self.ai_feed.update_content(feed_cards)

    async def _trigger_update_async(self, document_text: str) -> None:
        """
        Trigger an async update to the AI feed and ghost text.

        Makes HTTP request to backend server to get cards.

        Args:
            document_text: The current document text content
        """
        if self._update_in_progress:
            logger.warning("Update already in progress, skipping...")
            return

        self._update_in_progress = True

        logger.info("Starting async update via backend server")

        try:
            # Call backend to get cards
            all_cards = await self._call_backend(document_text)

            # If backend call failed, use last successful cards (retry logic)
            if all_cards is None:
                logger.warning("Backend call failed, using last successful cards")
                all_cards = self._last_successful_cards
            else:
                # Cache successful response
                self._last_successful_cards = all_cards

            if not all_cards:
                logger.info("No cards to process")
                self._update_in_progress = False
                return

            logger.info(f"Total cards received: {len(all_cards)}")

            # Backend manages card ordering and limits, so just replace the entire feed
            # This ensures consistency with polling updates from /cached endpoint
            self._update_ui_with_cards(all_cards)

        except Exception as e:
            logger.error(f"Error during update: {e}", exc_info=True)
        finally:
            self._update_in_progress = False
            logger.info("Update cycle completed")

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
