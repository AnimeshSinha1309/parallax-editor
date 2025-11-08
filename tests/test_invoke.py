"""Test script for the generic Fulfiller forward method."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fulfillers import Fulfiller, Card
from fulfillers.codesearch import CodeSearch
from utils.context import GlobalPreferenceContext


async def test_forward_basic():
    """Test basic forward functionality."""
    print("Test 1: Basic forward with query")
    try:
        search = CodeSearch()

        # Check if it's a Fulfiller
        assert isinstance(search, Fulfiller), "CodeSearch should be a Fulfiller"
        print("✓ CodeSearch is a Fulfiller")

        # Test forward method
        global_context = GlobalPreferenceContext(scope_root="../fulfillers")
        cards = await search.forward(
            document_text="# This is a sample file\ndef main():\n    pass",
            cursor_position=(2, 4),
            global_context=global_context,
            intent_label="class",
        )

        assert isinstance(cards, list), "forward should return a list"
        print(f"✓ forward returned {len(cards)} cards")

        if cards:
            assert all(isinstance(card, Card) for card in cards), "All items should be Card objects"
            print(f"✓ All {len(cards)} items are Card objects")

            # Print first card
            first_card = cards[0]
            print(f"\nFirst card:")
            print(f"  Header: {first_card.header}")
            print(f"  Text preview: {first_card.text[:80]}...")
            print(f"  Metadata: {first_card.metadata}")

    except Exception as e:
        print(f"✗ Error: {e}")
        raise


async def test_forward_with_kwargs():
    """Test forward with additional kwargs."""
    print("\n\nTest 2: Forward with custom parameters")
    try:
        search = CodeSearch(max_results=5)

        global_context = GlobalPreferenceContext(scope_root="../fulfillers")
        cards = await search.forward(
            document_text="",
            cursor_position=(0, 0),
            global_context=global_context,
            intent_label="def",
            max_results=3,  # Override default
        )

        print(f"✓ forward with max_results=3 returned {len(cards)} cards")
        assert len(cards) <= 3, "Should respect max_results"

    except Exception as e:
        print(f"✗ Error: {e}")
        raise


async def test_forward_error_handling():
    """Test forward error handling."""
    print("\n\nTest 3: Error handling")
    try:
        search = CodeSearch()

        # Invalid regex should return error card
        global_context = GlobalPreferenceContext(scope_root="../fulfillers")
        cards = await search.forward(
            document_text="",
            cursor_position=(0, 0),
            global_context=global_context,
            intent_label="[invalid(",
        )

        assert len(cards) == 1, "Error should return single card"
        assert cards[0].header == "Search Error", "Should return error card"
        print(f"✓ Error handling works: {cards[0].text}")

    except Exception as e:
        print(f"✗ Error: {e}")
        raise


async def test_forward_no_results():
    """Test forward with no matches."""
    print("\n\nTest 4: No results handling")
    try:
        search = CodeSearch()

        global_context = GlobalPreferenceContext(scope_root="../fulfillers")
        cards = await search.forward(
            document_text="",
            cursor_position=(0, 0),
            global_context=global_context,
            intent_label="xyzabc123impossible",
        )

        assert len(cards) == 1, "No results should return single card"
        assert cards[0].header == "No Results", "Should return no results card"
        print(f"✓ No results handling works: {cards[0].text}")

    except Exception as e:
        print(f"✗ Error: {e}")
        raise


async def main():
    print("Testing Fulfiller forward() Implementation")
    print("=" * 50)

    # Check if ripgrep is available
    search = CodeSearch()
    if not await search.is_available():
        print("✗ ripgrep is not installed or not in PATH")
        return

    await test_forward_basic()
    await test_forward_with_kwargs()
    await test_forward_error_handling()
    await test_forward_no_results()

    print("\n" + "=" * 50)
    print("All forward tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
