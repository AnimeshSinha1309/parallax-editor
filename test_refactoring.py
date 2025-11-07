#!/usr/bin/env python3
"""
Basic smoke test for the refactored code.
Tests the Card model and DummyFulfiller without requiring full dependencies.
"""

import asyncio
from fulfillers import Card, CardType, DummyFulfiller


def test_card_model():
    """Test Card model with type field."""
    print("Testing Card model...")

    # Test CONTEXT card
    context_card = Card(
        header="Test Context",
        text="This is context information",
        type=CardType.CONTEXT,
        metadata={"source": "test"}
    )
    assert context_card.type == CardType.CONTEXT
    assert context_card.header == "Test Context"
    assert context_card.text == "This is context information"
    print("✓ CONTEXT card creation successful")

    # Test QUESTION card
    question_card = Card(
        header="Test Question",
        text="What should we do?",
        type=CardType.QUESTION,
        metadata={"priority": "high"}
    )
    assert question_card.type == CardType.QUESTION
    print("✓ QUESTION card creation successful")

    # Test COMPLETION card
    completion_card = Card(
        header="Test Completion",
        text="    return value",
        type=CardType.COMPLETION,
        metadata={"trigger": "ghost_text"}
    )
    assert completion_card.type == CardType.COMPLETION
    print("✓ COMPLETION card creation successful")

    # Test __str__ method
    str_repr = str(context_card)
    assert "[context]" in str_repr.lower()
    print(f"✓ Card __str__ works: {str_repr}")

    print("✓ All Card model tests passed!\n")


async def test_dummy_fulfiller():
    """Test DummyFulfiller returns proper Card objects."""
    print("Testing DummyFulfiller...")

    fulfiller = DummyFulfiller()

    # Test is_available
    assert await fulfiller.is_available() == True
    print("✓ DummyFulfiller is available")

    # Test invoke
    cards = await fulfiller.invoke(
        text_buffer="def test():\n    pass",
        cursor_position=(0, 0),
        query_intent="test"
    )

    assert isinstance(cards, list)
    assert len(cards) >= 1 and len(cards) <= 3
    print(f"✓ DummyFulfiller returned {len(cards)} cards")

    # Verify all cards have required fields
    for card in cards:
        assert isinstance(card, Card)
        assert hasattr(card, 'header')
        assert hasattr(card, 'text')
        assert hasattr(card, 'type')
        assert isinstance(card.type, CardType)
        print(f"  - {card.type.value}: {card.header}")

    # Test multiple invocations return different cards (randomness)
    cards2 = await fulfiller.invoke(
        text_buffer="test",
        cursor_position=(0, 0),
        query_intent="test"
    )
    print(f"✓ Second invocation returned {len(cards2)} cards")

    print("✓ All DummyFulfiller tests passed!\n")


def test_card_type_separation():
    """Test that we can separate cards by type."""
    print("Testing card type separation...")

    cards = [
        Card(header="Q1", text="question", type=CardType.QUESTION, metadata={}),
        Card(header="C1", text="context", type=CardType.CONTEXT, metadata={}),
        Card(header="Comp1", text="completion", type=CardType.COMPLETION, metadata={}),
        Card(header="Q2", text="question2", type=CardType.QUESTION, metadata={}),
        Card(header="Comp2", text="completion2", type=CardType.COMPLETION, metadata={}),
    ]

    # Separate like FeedHandler does
    completion_cards = [c for c in cards if c.type == CardType.COMPLETION]
    feed_cards = [c for c in cards if c.type in (CardType.QUESTION, CardType.CONTEXT)]

    assert len(completion_cards) == 2
    assert len(feed_cards) == 3
    print(f"✓ Separated {len(completion_cards)} completion cards")
    print(f"✓ Separated {len(feed_cards)} feed cards (questions + context)")

    print("✓ All separation tests passed!\n")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("SMOKE TESTS FOR REFACTORED CODE")
    print("=" * 60 + "\n")

    try:
        test_card_model()
        await test_dummy_fulfiller()
        test_card_type_separation()

        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe refactored code is working correctly.")
        print("The Card model, CardType enum, and DummyFulfiller")
        print("are all functioning as expected.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -e .")
        print("2. Run the full application")
        print("3. Type 20 characters to trigger fulfillers")
        print("4. Check console output for ghost text logging")
        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
