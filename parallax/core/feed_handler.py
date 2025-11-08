"""
Feed handler for dynamic updates based on editor activity.
"""

import asyncio
import random
import logging
from typing import Optional, List, Tuple
from textual.widgets import TextArea
from parallax.core.suggestion_tracker import SuggestionTracker
from fulfillers import Fulfiller, Card, CardType
from utils.context import GlobalPreferenceContext
from utils.cards_refiner import CardsRefinerWrapper

logger = logging.getLogger("parallax.feed_handler")


class FeedHandler:
    """
    Handles dynamic updates to the AI feed based on editor activity.

    Tracks character changes and triggers updates after a specified threshold.
    Uses registered fulfillers to generate cards asynchronously.
    """

    def __init__(self, threshold: int = 20, global_context: GlobalPreferenceContext = None, idle_timeout: float = 4.0, enable_refiner: bool = False, max_cards_per_type: int = 3):
        """
        Initialize the feed handler.

        Args:
            threshold: Number of characters to type before triggering an update
            global_context: Global preference context containing scope root and plan path
            idle_timeout: Time in seconds to wait after last keystroke before triggering completion
            enable_refiner: Whether to use CardsRefiner for intelligent card merging (default: True)
            max_cards_per_type: Maximum number of cards to keep per card type (default: 3)
        """
        # Use default context if none provided
        if global_context is None:
            global_context = GlobalPreferenceContext(scope_root=".", plan_path=None)

        logger.info(f"Initializing FeedHandler with threshold={threshold}, scope_root={global_context.scope_root}, plan_path={global_context.plan_path}, idle_timeout={idle_timeout}s, enable_refiner={enable_refiner}, max_cards_per_type={max_cards_per_type}")
        self.threshold = threshold
        self.idle_timeout = idle_timeout
        self.char_count = 0
        self.last_content = ""
        self.cursor_position: Tuple[int, int] = (0, 0)
        self.global_context = global_context
        self.ai_feed = None
        self.text_editor = None
        self.feed_items: List[Card] = []
        self.suggestion_tracker = SuggestionTracker()
        self.immediate_fulfillers: List[Fulfiller] = []  # Triggered immediately after threshold
        self.idle_fulfillers: List[Fulfiller] = []  # Triggered after idle timeout
        self._update_in_progress = False
        self._immediate_update_in_progress = False
        self._last_completion_triggered = False
        self._idle_task: Optional[asyncio.Task] = None
        self._ignoring_next_change = False
        self.enable_refiner = enable_refiner
        self.max_cards_per_type = max_cards_per_type
        self.cards_refiner = CardsRefinerWrapper(max_cards_per_type=max_cards_per_type)
        logger.debug(f"CardsRefinerWrapper initialized (enabled={enable_refiner}, max_cards_per_type={max_cards_per_type})")

    def register_fulfiller(self, fulfiller: Fulfiller, trigger_type: str = "idle") -> None:
        """
        Register a fulfiller to be invoked during updates.

        Args:
            fulfiller: A Fulfiller instance to register
            trigger_type: "immediate" for threshold-based trigger, "idle" for idle-timeout-based trigger
        """
        fulfiller_name = fulfiller.__class__.__name__
        logger.info(f"Registering fulfiller: {fulfiller_name} with trigger_type={trigger_type}")

        if trigger_type == "immediate":
            self.immediate_fulfillers.append(fulfiller)
        elif trigger_type == "idle":
            self.idle_fulfillers.append(fulfiller)
        else:
            logger.error(f"Invalid trigger_type: {trigger_type}. Must be 'immediate' or 'idle'")
            return

        total_fulfillers = len(self.immediate_fulfillers) + len(self.idle_fulfillers)
        logger.debug(f"Total registered fulfillers: {total_fulfillers} (immediate={len(self.immediate_fulfillers)}, idle={len(self.idle_fulfillers)})")

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
            logger.info(f"Threshold reached ({self.char_count} >= {self.threshold})")

            # Trigger immediate fulfillers right away
            if self.immediate_fulfillers:
                logger.info(f"Triggering {len(self.immediate_fulfillers)} immediate fulfiller(s)")
                asyncio.create_task(self._trigger_immediate_update_async(new_content))

            # Start idle timer for idle fulfillers
            if self.idle_fulfillers:
                logger.info(f"Starting {self.idle_timeout}s idle timer for {len(self.idle_fulfillers)} idle fulfiller(s)")
                self._idle_task = asyncio.create_task(self._wait_and_trigger_idle(new_content))
        elif self._last_completion_triggered:
            logger.debug("Completion already triggered, not starting new timer")

    async def _wait_and_trigger_idle(self, document_text: str) -> None:
        """
        Wait for idle timeout, then trigger idle fulfillers if still idle.

        Args:
            document_text: The current document text content
        """
        try:
            logger.debug(f"Waiting {self.idle_timeout}s for idle timeout...")
            await asyncio.sleep(self.idle_timeout)
            logger.info("Idle timeout elapsed, triggering idle fulfillers")
            await self._trigger_update_async(document_text, self.idle_fulfillers, "idle")
            # Reset counter after successful trigger
            self.char_count = 0
        except asyncio.CancelledError:
            logger.debug("Idle timer cancelled (user continued typing)")
            # Don't reset counter - keep accumulating

    async def _trigger_immediate_update_async(self, document_text: str) -> None:
        """
        Trigger immediate fulfillers (threshold-based).

        Args:
            document_text: The current document text content
        """
        await self._trigger_update_async(document_text, self.immediate_fulfillers, "immediate")
        # Reset counter after successful trigger
        self.char_count = 0

    async def _trigger_update_async(self, document_text: str, fulfillers: List[Fulfiller], fulfiller_type: str) -> None:
        """
        Trigger an async update to the AI feed and ghost text.

        Invokes specified fulfillers concurrently and processes their results.

        Args:
            document_text: The current document text content
            fulfillers: List of fulfillers to invoke
            fulfiller_type: Type of fulfillers being invoked ("immediate" or "idle")
        """
        # Use different locks for immediate vs idle to avoid blocking each other
        if fulfiller_type == "immediate":
            if self._immediate_update_in_progress:
                logger.warning("Immediate update already in progress, skipping...")
                return
            self._immediate_update_in_progress = True
        else:
            if self._update_in_progress:
                logger.warning("Idle update already in progress, skipping...")
                return
            self._update_in_progress = True

        if not fulfillers:
            logger.warning(f"No {fulfiller_type} fulfillers registered, skipping update")
            if fulfiller_type == "immediate":
                self._immediate_update_in_progress = False
            else:
                self._update_in_progress = False
            return

        logger.info(f"Starting async {fulfiller_type} update with {len(fulfillers)} fulfiller(s)")

        try:
            # Invoke all fulfillers concurrently
            logger.debug(f"Invoking {fulfiller_type} fulfillers with cursor_position={self.cursor_position}, global_context={self.global_context}")
            tasks = [
                fulfiller.forward(
                    document_text=document_text,
                    cursor_position=self.cursor_position,
                    global_context=self.global_context,
                    intent_label="editor_update"
                )
                for fulfiller in fulfillers
            ]

            logger.info("Gathering results from all fulfillers...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Received {len(results)} results from fulfillers")

            # Flatten all cards from all fulfillers
            all_cards: List[Card] = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Fulfiller {i} error: {result}", exc_info=result)
                    continue
                if isinstance(result, list):
                    logger.debug(f"Fulfiller {i} returned {len(result)} card(s)")
                    all_cards.extend(result)

            logger.info(f"Total cards received: {len(all_cards)}")

            # Separate cards by type
            completion_cards = [c for c in all_cards if c.type == CardType.COMPLETION]
            feed_cards = [c for c in all_cards if c.type in (CardType.QUESTION, CardType.CONTEXT)]

            logger.info(f"Separated cards: {len(completion_cards)} COMPLETION, {len(feed_cards)} QUESTION/CONTEXT")

            # Handle ghost text completions
            if completion_cards:
                logger.info(f"Processing {len(completion_cards)} completion card(s) for ghost text")
                if self.text_editor:
                    # Use the first completion card
                    completion_text = completion_cards[0].text
                    logger.info(f"Setting ghost text: {completion_text[:50]}...")
                    self.text_editor.set_ghost_text(completion_text)
                    # Mark that we've triggered a completion - don't trigger again until user interacts
                    self._last_completion_triggered = True
                    logger.debug("Ghost text set successfully, completion flag set")
                else:
                    logger.error("TextEditor not set, cannot render ghost text")
            else:
                logger.debug("No completion cards received")

            # Handle feed cards - update the sidebar
            if feed_cards:
                logger.info(f"Processing {len(feed_cards)} feed card(s) for sidebar")

                if self.enable_refiner:
                    # Use CardsRefiner to intelligently merge existing and new cards
                    logger.debug(f"Refining cards: {len(self.feed_items)} existing, {len(feed_cards)} new")
                    refined_cards = self.cards_refiner.refine_cards(
                        existing_cards=self.feed_items,
                        newly_proposed_cards=feed_cards
                    )
                    logger.info(f"Cards refined: {len(refined_cards)} cards after refinement")
                    self.feed_items = refined_cards
                else:
                    # Refiner disabled - delete all old cards and keep only new ones
                    logger.info("CardsRefiner disabled, replacing all existing cards with new ones")
                    self.feed_items = feed_cards

                # Update the AI feed widget
                if self.ai_feed:
                    logger.debug("Updating AI feed widget with refined cards")
                    self.ai_feed.update_content(self.feed_items)
                else:
                    logger.warning("AI feed not set, cannot update sidebar")
            else:
                logger.debug("No feed cards to process")

        except Exception as e:
            logger.error(f"Error during {fulfiller_type} update: {e}", exc_info=True)
        finally:
            if fulfiller_type == "immediate":
                self._immediate_update_in_progress = False
            else:
                self._update_in_progress = False
            logger.info(f"{fulfiller_type.capitalize()} update cycle completed")

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
