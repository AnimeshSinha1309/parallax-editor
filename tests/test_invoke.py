"""Test script for the generic Fulfiller invoke method."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fulfillers import Fulfiller, Card
from fulfillers.codesearch import CodeSearch


async def test_invoke_basic():
    """Test basic invoke functionality."""
    print("Test 1: Basic invoke with query")
    try:
        search = CodeSearch()

        # Check if it's a Fulfiller
        assert isinstance(search, Fulfiller), "CodeSearch should be a Fulfiller"
        print("✓ CodeSearch is a Fulfiller")

        # Test invoke method
        cards = await search.invoke(
            text_buffer="# This is a sample file\ndef main():\n    pass",
            cursor_position=(2, 4),
            query_intent="class",
            context="../fulfillers",
        )

        assert isinstance(cards, list), "invoke should return a list"
        print(f"✓ invoke returned {len(cards)} cards")

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


async def test_invoke_with_kwargs():
    """Test invoke with additional kwargs."""
    print("\n\nTest 2: Invoke with custom parameters")
    try:
        search = CodeSearch(max_results=5)

        cards = await search.invoke(
            text_buffer="",
            cursor_position=(0, 0),
            query_intent="def",
            context="../fulfillers",
            max_results=3,  # Override default
        )

        print(f"✓ invoke with max_results=3 returned {len(cards)} cards")
        assert len(cards) <= 3, "Should respect max_results"

    except Exception as e:
        print(f"✗ Error: {e}")
        raise


async def test_invoke_error_handling():
    """Test invoke error handling."""
    print("\n\nTest 3: Error handling")
    try:
        search = CodeSearch()

        # Invalid regex should return error card
        cards = await search.invoke(
            text_buffer="",
            cursor_position=(0, 0),
            query_intent="[invalid(",
            context="../fulfillers",
        )

        assert len(cards) == 1, "Error should return single card"
        assert cards[0].header == "Search Error", "Should return error card"
        print(f"✓ Error handling works: {cards[0].text}")

    except Exception as e:
        print(f"✗ Error: {e}")
        raise


async def test_invoke_no_results():
    """Test invoke with no matches."""
    print("\n\nTest 4: No results handling")
    try:
        search = CodeSearch()

        cards = await search.invoke(
            text_buffer="",
            cursor_position=(0, 0),
            query_intent="xyzabc123impossible",
            context="../fulfillers",
        )

        assert len(cards) == 1, "No results should return single card"
        assert cards[0].header == "No Results", "Should return no results card"
        print(f"✓ No results handling works: {cards[0].text}")

    except Exception as e:
        print(f"✗ Error: {e}")
        raise


async def main():
    print("Testing Fulfiller invoke() Implementation")
    print("=" * 50)

    # Check if ripgrep is available
    search = CodeSearch()
    if not await search.is_available():
        print("✗ ripgrep is not installed or not in PATH")
        return

    await test_invoke_basic()
    await test_invoke_with_kwargs()
    await test_invoke_error_handling()
    await test_invoke_no_results()

    print("\n" + "=" * 50)
    print("All invoke tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
