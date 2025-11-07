"""
Tests for the FeedHandler class.
"""

import pytest
from parallax.core.feed_handler import FeedHandler


class MockAIFeed:
    """Mock AI feed for testing."""

    def __init__(self):
        self.config = [
            {"header": "Item 1", "content": "Content 1"},
            {"header": "Item 2", "content": "Content 2"},
            {"header": "Item 3", "content": "Content 3"},
        ]
        self.update_count = 0

    def update_content(self, new_config):
        """Update the feed content."""
        self.config = new_config
        self.update_count += 1


def test_feed_handler_initialization():
    """Test that FeedHandler initializes correctly."""
    handler = FeedHandler(threshold=20)
    assert handler.threshold == 20
    assert handler.char_count == 0
    assert handler.last_content == ""
    assert handler.ai_feed is None


def test_feed_handler_custom_threshold():
    """Test FeedHandler with custom threshold."""
    handler = FeedHandler(threshold=50)
    assert handler.threshold == 50


def test_set_ai_feed():
    """Test setting the AI feed."""
    handler = FeedHandler()
    mock_feed = MockAIFeed()
    handler.set_ai_feed(mock_feed)

    assert handler.ai_feed is mock_feed
    assert len(handler.feed_items) == 3


def test_char_count_tracking():
    """Test that character changes are tracked correctly."""
    handler = FeedHandler(threshold=100)
    handler.on_text_change("Hello")
    assert handler.char_count == 5

    handler.on_text_change("Hello World")
    assert handler.char_count == 11


def test_trigger_on_threshold():
    """Test that updates trigger after reaching threshold."""
    handler = FeedHandler(threshold=20)
    mock_feed = MockAIFeed()
    handler.set_ai_feed(mock_feed)

    initial_update_count = mock_feed.update_count

    # Type 10 characters - should not trigger
    handler.on_text_change("1234567890")
    assert mock_feed.update_count == initial_update_count

    # Type 15 more characters (total content is now 25 chars) - should trigger
    handler.on_text_change("1234567890123456789012345")
    assert mock_feed.update_count == initial_update_count + 1

    # Counter should be reset
    assert handler.char_count < 20


def test_push_item():
    """Test manually pushing items to the feed."""
    handler = FeedHandler()
    mock_feed = MockAIFeed()
    handler.set_ai_feed(mock_feed)

    initial_count = len(handler.feed_items)
    handler.push_item("New Header", "New Content")

    assert len(handler.feed_items) == initial_count + 1
    assert handler.feed_items[-1]["header"] == "New Header"
    assert handler.feed_items[-1]["content"] == "New Content"


def test_push_item_at_position():
    """Test pushing items at specific positions."""
    handler = FeedHandler()
    mock_feed = MockAIFeed()
    handler.set_ai_feed(mock_feed)

    handler.push_item("Inserted", "At position 1", position=1)

    assert handler.feed_items[1]["header"] == "Inserted"
    assert len(handler.feed_items) == 4


def test_delete_item():
    """Test deleting items from the feed."""
    handler = FeedHandler()
    mock_feed = MockAIFeed()
    handler.set_ai_feed(mock_feed)

    initial_count = len(handler.feed_items)
    result = handler.delete_item(1)

    assert result is True
    assert len(handler.feed_items) == initial_count - 1


def test_delete_item_out_of_range():
    """Test deleting items with invalid index."""
    handler = FeedHandler()
    mock_feed = MockAIFeed()
    handler.set_ai_feed(mock_feed)

    result = handler.delete_item(100)
    assert result is False


def test_reset_counter():
    """Test resetting the character counter."""
    handler = FeedHandler()
    handler.on_text_change("Some text")

    assert handler.char_count > 0
    handler.reset_counter()
    assert handler.char_count == 0


def test_get_counter():
    """Test getting the current counter value."""
    handler = FeedHandler()
    handler.on_text_change("12345")

    assert handler.get_counter() == 5


def test_trigger_adds_and_removes_items():
    """Test that triggering both removes an old item and adds a new one."""
    handler = FeedHandler(threshold=20)
    mock_feed = MockAIFeed()
    handler.set_ai_feed(mock_feed)

    initial_count = len(handler.feed_items)

    # Trigger an update
    handler.on_text_change("12345678901234567890")

    # Should have same count (one removed, one added)
    assert len(handler.feed_items) == initial_count


def test_multiple_triggers():
    """Test multiple consecutive triggers."""
    handler = FeedHandler(threshold=10)
    mock_feed = MockAIFeed()
    handler.set_ai_feed(mock_feed)

    # Trigger multiple times
    for i in range(5):
        handler.on_text_change("x" * (10 * (i + 1)))

    # Should have triggered 5 times
    assert mock_feed.update_count >= 5
