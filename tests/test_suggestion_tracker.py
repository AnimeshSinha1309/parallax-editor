"""
Tests for the SuggestionTracker class.
"""

import pytest
import tempfile
import os
from pathlib import Path
from parallax.core.suggestion_tracker import SuggestionTracker


@pytest.fixture
def temp_storage_file():
    """Create a temporary storage file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    yield temp_file
    # Cleanup
    if os.path.exists(temp_file):
        os.remove(temp_file)


def test_initialization(temp_storage_file):
    """Test that SuggestionTracker initializes correctly."""
    tracker = SuggestionTracker(storage_file=temp_storage_file)
    assert tracker.deleted_suggestions == set()


def test_mark_deleted(temp_storage_file):
    """Test marking a suggestion as deleted."""
    tracker = SuggestionTracker(storage_file=temp_storage_file)
    tracker.mark_deleted("Test Header", "Test Content")

    assert tracker.is_deleted("Test Header", "Test Content")
    assert tracker.get_deleted_count() == 1


def test_is_deleted(temp_storage_file):
    """Test checking if a suggestion is deleted."""
    tracker = SuggestionTracker(storage_file=temp_storage_file)

    # Not deleted initially
    assert not tracker.is_deleted("Header", "Content")

    # Mark as deleted
    tracker.mark_deleted("Header", "Content")

    # Now it should be deleted
    assert tracker.is_deleted("Header", "Content")


def test_multiple_deletions(temp_storage_file):
    """Test marking multiple suggestions as deleted."""
    tracker = SuggestionTracker(storage_file=temp_storage_file)

    tracker.mark_deleted("Header 1", "Content 1")
    tracker.mark_deleted("Header 2", "Content 2")
    tracker.mark_deleted("Header 3", "Content 3")

    assert tracker.get_deleted_count() == 3
    assert tracker.is_deleted("Header 1", "Content 1")
    assert tracker.is_deleted("Header 2", "Content 2")
    assert tracker.is_deleted("Header 3", "Content 3")


def test_unique_key_generation(temp_storage_file):
    """Test that unique keys are generated correctly."""
    tracker = SuggestionTracker(storage_file=temp_storage_file)

    # Different header, same content
    tracker.mark_deleted("Header A", "Content")
    assert tracker.is_deleted("Header A", "Content")
    assert not tracker.is_deleted("Header B", "Content")

    # Same header, different content
    tracker.mark_deleted("Header", "Content A")
    assert tracker.is_deleted("Header", "Content A")
    assert not tracker.is_deleted("Header", "Content B")


def test_clear_all(temp_storage_file):
    """Test clearing all deleted suggestions."""
    tracker = SuggestionTracker(storage_file=temp_storage_file)

    tracker.mark_deleted("Header 1", "Content 1")
    tracker.mark_deleted("Header 2", "Content 2")

    assert tracker.get_deleted_count() == 2

    tracker.clear_all()

    assert tracker.get_deleted_count() == 0
    assert not tracker.is_deleted("Header 1", "Content 1")
    assert not tracker.is_deleted("Header 2", "Content 2")


def test_persistence(temp_storage_file):
    """Test that deleted suggestions persist across instances."""
    # Create tracker and mark some suggestions as deleted
    tracker1 = SuggestionTracker(storage_file=temp_storage_file)
    tracker1.mark_deleted("Persistent Header", "Persistent Content")
    tracker1.mark_deleted("Another Header", "Another Content")

    # Create a new tracker instance with the same storage file
    tracker2 = SuggestionTracker(storage_file=temp_storage_file)

    # Should load the deleted suggestions
    assert tracker2.is_deleted("Persistent Header", "Persistent Content")
    assert tracker2.is_deleted("Another Header", "Another Content")
    assert tracker2.get_deleted_count() == 2


def test_corrupted_file_handling(temp_storage_file):
    """Test handling of corrupted storage file."""
    # Write invalid JSON to the file
    with open(temp_storage_file, 'w') as f:
        f.write("{ invalid json }")

    # Should not crash, just start with empty set
    tracker = SuggestionTracker(storage_file=temp_storage_file)
    assert tracker.get_deleted_count() == 0


def test_missing_file():
    """Test handling when storage file doesn't exist."""
    # Use a file that doesn't exist
    non_existent_file = ".non_existent_test_file.json"

    # Should not crash, just start with empty set
    tracker = SuggestionTracker(storage_file=non_existent_file)
    assert tracker.get_deleted_count() == 0

    # Clean up if it was created
    file_path = Path.home() / non_existent_file
    if file_path.exists():
        file_path.unlink()


def test_duplicate_deletions(temp_storage_file):
    """Test that marking the same suggestion multiple times doesn't duplicate."""
    tracker = SuggestionTracker(storage_file=temp_storage_file)

    tracker.mark_deleted("Header", "Content")
    tracker.mark_deleted("Header", "Content")
    tracker.mark_deleted("Header", "Content")

    # Should only count as one deletion (sets don't allow duplicates)
    assert tracker.get_deleted_count() == 1


def test_special_characters(temp_storage_file):
    """Test handling of special characters in headers and content."""
    tracker = SuggestionTracker(storage_file=temp_storage_file)

    header = "Test: Header with \"quotes\" and 'apostrophes'"
    content = "Content with\nnewlines\nand\ttabs"

    tracker.mark_deleted(header, content)
    assert tracker.is_deleted(header, content)
