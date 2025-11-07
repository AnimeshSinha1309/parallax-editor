"""
Unit tests for the AI feed configuration.
"""

import pytest
from parallax.config.ai_config import (
    AI_FEED_CONFIG,
    get_ai_feed_config,
    update_ai_feed_config,
    add_info_box
)


class TestAIFeedConfig:
    """Test suite for AI feed configuration."""

    def setup_method(self):
        """Set up test fixtures."""
        # Store the original config to restore after each test
        self.original_config = AI_FEED_CONFIG.copy()

    def teardown_method(self):
        """Restore original config after each test."""
        update_ai_feed_config(self.original_config)

    def test_default_config_exists(self):
        """Test that default configuration exists."""
        assert AI_FEED_CONFIG is not None
        assert isinstance(AI_FEED_CONFIG, list)
        assert len(AI_FEED_CONFIG) > 0

    def test_default_config_structure(self):
        """Test that default configuration has correct structure."""
        for box in AI_FEED_CONFIG:
            assert isinstance(box, dict)
            assert "header" in box
            assert "content" in box
            assert isinstance(box["header"], str)
            assert isinstance(box["content"], str)
            assert len(box["header"]) > 0
            assert len(box["content"]) > 0

    def test_get_ai_feed_config(self):
        """Test getting the AI feed configuration."""
        config = get_ai_feed_config()
        assert isinstance(config, list)
        assert len(config) > 0
        assert config == AI_FEED_CONFIG

    def test_update_ai_feed_config(self):
        """Test updating the AI feed configuration."""
        new_config = [
            {"header": "Test Header", "content": "Test content"}
        ]
        update_ai_feed_config(new_config)
        config = get_ai_feed_config()
        assert config == new_config
        assert len(config) == 1
        assert config[0]["header"] == "Test Header"

    def test_add_info_box(self):
        """Test adding a new information box."""
        original_length = len(get_ai_feed_config())
        add_info_box("New Header", "New content")
        config = get_ai_feed_config()
        assert len(config) == original_length + 1
        assert config[-1]["header"] == "New Header"
        assert config[-1]["content"] == "New content"

    def test_multiple_info_boxes(self):
        """Test adding multiple information boxes."""
        original_length = len(get_ai_feed_config())
        add_info_box("Header 1", "Content 1")
        add_info_box("Header 2", "Content 2")
        config = get_ai_feed_config()
        assert len(config) == original_length + 2

    def test_config_persistence_across_calls(self):
        """Test that config changes persist across function calls."""
        new_config = [{"header": "Test", "content": "Test"}]
        update_ai_feed_config(new_config)
        config1 = get_ai_feed_config()
        config2 = get_ai_feed_config()
        assert config1 == config2

    def test_default_headers_present(self):
        """Test that default configuration includes expected headers."""
        config = get_ai_feed_config()
        headers = [box["header"] for box in config]
        # Check for some expected default headers
        assert any("Information" in h for h in headers)
        assert any("References" in h for h in headers)

    def test_empty_config_update(self):
        """Test updating with empty configuration."""
        update_ai_feed_config([])
        config = get_ai_feed_config()
        assert config == []
        assert len(config) == 0

    def test_add_info_box_to_empty_config(self):
        """Test adding info box to empty configuration."""
        update_ai_feed_config([])
        add_info_box("First", "Content")
        config = get_ai_feed_config()
        assert len(config) == 1
        assert config[0]["header"] == "First"

    def test_config_box_content_types(self):
        """Test that all content in default config is string type."""
        config = get_ai_feed_config()
        for box in config:
            assert isinstance(box["header"], str)
            assert isinstance(box["content"], str)

    def test_add_info_box_with_multiline_content(self):
        """Test adding info box with multiline content."""
        multiline_content = "Line 1\nLine 2\nLine 3"
        add_info_box("Multiline", multiline_content)
        config = get_ai_feed_config()
        assert config[-1]["content"] == multiline_content
        assert "\n" in config[-1]["content"]

    def test_update_with_special_characters(self):
        """Test updating config with special characters."""
        special_config = [
            {"header": "Test & <Test>", "content": "Content with 'quotes' and \"quotes\""}
        ]
        update_ai_feed_config(special_config)
        config = get_ai_feed_config()
        assert config[0]["header"] == "Test & <Test>"
        assert "quotes" in config[0]["content"]
