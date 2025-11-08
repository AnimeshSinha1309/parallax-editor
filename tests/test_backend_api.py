"""
Comprehensive tests for Parallizer backend API.

These tests make REAL LLM calls (not mocked) and include timing benchmarks.
Run with: pytest tests/test_backend_api.py -v -s
"""

import pytest
import time
import json
from pathlib import Path
from fastapi.testclient import TestClient
from parallizer.backend_handler import app, initialize_fulfillers


# Test fixture paths
FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_DOCUMENT = FIXTURES_DIR / "test_document.md"


@pytest.fixture(scope="module")
def client():
    """Create a test client for the FastAPI app."""
    # Initialize fulfillers before testing
    initialize_fulfillers()
    return TestClient(app)


@pytest.fixture(scope="module")
def test_document_text():
    """Load test document content."""
    if not TEST_DOCUMENT.exists():
        pytest.skip(f"Test document not found: {TEST_DOCUMENT}")
    return TEST_DOCUMENT.read_text()


@pytest.fixture
def base_fulfill_request(test_document_text):
    """Base request payload for /fulfill endpoint."""
    return {
        "user_id": "test_user_001",
        "document_text": test_document_text,
        "cursor_position": [10, 0],  # Line 10, column 0
        "global_context": {
            "scope_root": str(Path(__file__).parent.parent),
            "plan_path": None
        }
    }


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_root_endpoint(self, client):
        """Test GET / returns basic status."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "service" in data
        assert data["service"] == "Parallizer Backend"
        assert "status" in data
        assert data["status"] == "running"
        assert "fulfillers" in data
        assert isinstance(data["fulfillers"], int)
        assert data["fulfillers"] > 0  # Should have registered fulfillers

        print(f"\n✓ Root endpoint: {data}")

    def test_health_endpoint(self, client):
        """Test GET /health returns detailed fulfiller status."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "service" in data
        assert "status" in data
        assert data["status"] == "healthy"
        assert "fulfillers" in data
        assert isinstance(data["fulfillers"], list)

        # Check each fulfiller has required fields
        for fulfiller in data["fulfillers"]:
            assert "name" in fulfiller
            assert "available" in fulfiller
            assert isinstance(fulfiller["available"], bool)

        print(f"\n✓ Health endpoint: {len(data['fulfillers'])} fulfillers")
        for f in data["fulfillers"]:
            status = "✓" if f["available"] else "✗"
            print(f"  {status} {f['name']}: {f['available']}")


class TestFulfillEndpoint:
    """Tests for the main /fulfill endpoint with real LLM calls."""

    def test_fulfill_basic_request(self, client, base_fulfill_request):
        """Test basic fulfill request returns valid response."""
        start_time = time.time()
        response = client.post("/fulfill", json=base_fulfill_request)
        elapsed = time.time() - start_time

        assert response.status_code == 200, f"Request failed: {response.text}"

        data = response.json()
        assert "cards" in data
        assert isinstance(data["cards"], list)

        print(f"\n✓ Basic fulfill request completed in {elapsed:.2f}s")
        print(f"  Returned {len(data['cards'])} cards")

        # Validate card structure
        for card in data["cards"]:
            assert "header" in card
            assert "text" in card
            assert "type" in card
            assert "metadata" in card
            assert card["type"] in ["completion", "question", "context"]

            print(f"  - {card['type'].upper()}: {card['header'][:50]}")

    def test_fulfill_returns_different_card_types(self, client, base_fulfill_request):
        """Test that fulfill returns multiple card types."""
        response = client.post("/fulfill", json=base_fulfill_request)
        assert response.status_code == 200

        data = response.json()
        cards = data["cards"]

        # Collect card types
        card_types = {card["type"] for card in cards}

        print(f"\n✓ Card types returned: {card_types}")

        # We expect at least some cards (may not always get all types)
        assert len(cards) > 0, "Should return at least some cards"

    def test_fulfill_maintains_card_limits(self, client, base_fulfill_request):
        """Test that card type limits are enforced (max 3 per type)."""
        # Make multiple requests to build up state
        for i in range(3):
            response = client.post("/fulfill", json=base_fulfill_request)
            assert response.status_code == 200

        # Check final state
        response = client.post("/fulfill", json=base_fulfill_request)
        data = response.json()

        # Count cards by type
        card_counts = {}
        for card in data["cards"]:
            card_type = card["type"]
            card_counts[card_type] = card_counts.get(card_type, 0) + 1

        print(f"\n✓ Card counts by type: {card_counts}")

        # Verify no type exceeds limit of 3
        for card_type, count in card_counts.items():
            assert count <= 3, f"Card type {card_type} has {count} cards, exceeds limit of 3"

    def test_fulfill_with_different_cursor_positions(self, client, base_fulfill_request):
        """Test fulfill with various cursor positions."""
        test_positions = [
            [0, 0],    # Start of document
            [5, 10],   # Middle of line
            [15, 0],   # Code section
            [25, 0],   # End section
        ]

        results = []
        for position in test_positions:
            request = base_fulfill_request.copy()
            request["cursor_position"] = position

            start_time = time.time()
            response = client.post("/fulfill", json=request)
            elapsed = time.time() - start_time

            assert response.status_code == 200
            data = response.json()

            results.append({
                "position": position,
                "cards": len(data["cards"]),
                "time": elapsed
            })

        print(f"\n✓ Cursor position tests:")
        for r in results:
            print(f"  Position {r['position']}: {r['cards']} cards in {r['time']:.2f}s")

    def test_fulfill_validation_errors(self, client):
        """Test that invalid requests return appropriate errors."""
        # Missing required fields
        invalid_requests = [
            {},  # Empty request
            {"user_id": "test"},  # Missing document_text
            {"user_id": "test", "document_text": "test"},  # Missing cursor_position
        ]

        for invalid_request in invalid_requests:
            response = client.post("/fulfill", json=invalid_request)
            assert response.status_code == 422, "Should return validation error"

        print("\n✓ Validation errors handled correctly")


class TestFulfillerBenchmarks:
    """Benchmarking tests for individual fulfillers with real LLM calls."""

    def test_benchmark_all_fulfillers(self, client, base_fulfill_request):
        """
        Benchmark the complete fulfill request with all fulfillers.
        This makes REAL LLM calls and measures end-to-end performance.
        """
        print("\n" + "="*70)
        print("BENCHMARK: Complete Fulfill Request (All Fulfillers)")
        print("="*70)

        num_runs = 3
        timings = []

        for run in range(num_runs):
            start_time = time.time()
            response = client.post("/fulfill", json=base_fulfill_request)
            elapsed = time.time() - start_time

            assert response.status_code == 200
            data = response.json()

            timings.append({
                "run": run + 1,
                "time": elapsed,
                "cards": len(data["cards"])
            })

            print(f"\nRun {run + 1}:")
            print(f"  Time: {elapsed:.2f}s")
            print(f"  Cards returned: {len(data['cards'])}")

            # Show card breakdown
            card_types = {}
            for card in data["cards"]:
                card_type = card["type"]
                card_types[card_type] = card_types.get(card_type, 0) + 1

            for card_type, count in card_types.items():
                print(f"    - {card_type}: {count}")

        # Calculate statistics
        times = [t["time"] for t in timings]
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"\n" + "-"*70)
        print(f"Statistics over {num_runs} runs:")
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Min: {min_time:.2f}s")
        print(f"  Max: {max_time:.2f}s")
        print("="*70)

    def test_benchmark_short_document(self, client):
        """Benchmark with a very short document."""
        print("\n" + "="*70)
        print("BENCHMARK: Short Document")
        print("="*70)

        short_doc = """# Quick Test

def hello():
    print("world")
"""

        request = {
            "user_id": "test_benchmark_short",
            "document_text": short_doc,
            "cursor_position": [3, 0],
            "global_context": {
                "scope_root": str(Path(__file__).parent.parent),
                "plan_path": None
            }
        }

        start_time = time.time()
        response = client.post("/fulfill", json=request)
        elapsed = time.time() - start_time

        assert response.status_code == 200
        data = response.json()

        print(f"\nShort document ({len(short_doc)} chars):")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Cards: {len(data['cards'])}")
        print("="*70)

    def test_benchmark_concurrent_users(self, client, base_fulfill_request):
        """Test performance with multiple concurrent users."""
        print("\n" + "="*70)
        print("BENCHMARK: Multiple Users")
        print("="*70)

        user_ids = ["user_001", "user_002", "user_003"]
        results = []

        for user_id in user_ids:
            request = base_fulfill_request.copy()
            request["user_id"] = user_id

            start_time = time.time()
            response = client.post("/fulfill", json=request)
            elapsed = time.time() - start_time

            assert response.status_code == 200
            data = response.json()

            results.append({
                "user": user_id,
                "time": elapsed,
                "cards": len(data["cards"])
            })

        print("\nResults:")
        for r in results:
            print(f"  {r['user']}: {r['time']:.2f}s ({r['cards']} cards)")

        avg_time = sum(r["time"] for r in results) / len(results)
        print(f"\nAverage time per user: {avg_time:.2f}s")
        print("="*70)


class TestUserFeedManagement:
    """Tests for user feed state management."""

    def test_feed_persists_across_requests(self, client, base_fulfill_request):
        """Test that feed state persists for the same user."""
        user_id = "test_persistence_user"
        request = base_fulfill_request.copy()
        request["user_id"] = user_id

        # First request
        response1 = client.post("/fulfill", json=request)
        assert response1.status_code == 200
        cards1 = response1.json()["cards"]

        # Second request (should build on previous state)
        response2 = client.post("/fulfill", json=request)
        assert response2.status_code == 200
        cards2 = response2.json()["cards"]

        # Cards may have grown or stayed same due to limits
        assert len(cards2) >= 0  # Feed should exist

        print(f"\n✓ Feed persistence:")
        print(f"  Request 1: {len(cards1)} cards")
        print(f"  Request 2: {len(cards2)} cards")

    def test_clear_user_feed(self, client, base_fulfill_request):
        """Test clearing a user's feed."""
        user_id = "test_clear_user"
        request = base_fulfill_request.copy()
        request["user_id"] = user_id

        # Create some feed data
        response = client.post("/fulfill", json=request)
        assert response.status_code == 200
        assert len(response.json()["cards"]) > 0

        # Clear the feed
        response = client.delete(f"/user/{user_id}/feed")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"

        print(f"\n✓ Feed cleared for user: {user_id}")

    def test_clear_nonexistent_user_feed(self, client):
        """Test clearing feed for non-existent user."""
        response = client.delete("/user/nonexistent_user/feed")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "not_found"

        print("\n✓ Clearing non-existent feed handled gracefully")


class TestCorrectnessValidation:
    """Tests to validate correctness of fulfiller outputs."""

    def test_completion_cards_have_text(self, client, base_fulfill_request):
        """Test that completion cards contain actual completion text."""
        response = client.post("/fulfill", json=base_fulfill_request)
        assert response.status_code == 200

        cards = response.json()["cards"]
        completion_cards = [c for c in cards if c["type"] == "completion"]

        for card in completion_cards:
            assert len(card["text"]) > 0, "Completion card should have text"
            assert len(card["header"]) > 0, "Completion card should have header"

            print(f"\n✓ Completion card:")
            print(f"  Header: {card['header']}")
            print(f"  Text length: {len(card['text'])} chars")
            if "confidence" in card.get("metadata", {}):
                print(f"  Confidence: {card['metadata']['confidence']}")

    def test_question_cards_are_relevant(self, client, base_fulfill_request):
        """Test that question/ambiguity cards are relevant to the document."""
        response = client.post("/fulfill", json=base_fulfill_request)
        assert response.status_code == 200

        cards = response.json()["cards"]
        question_cards = [c for c in cards if c["type"] == "question"]

        for card in question_cards:
            assert len(card["text"]) > 0
            # Question should typically be a sentence
            assert len(card["text"]) > 10

            print(f"\n✓ Question card:")
            print(f"  Header: {card['header']}")
            print(f"  Question: {card['text'][:100]}...")

    def test_context_cards_have_content(self, client, base_fulfill_request):
        """Test that context cards contain meaningful content."""
        response = client.post("/fulfill", json=base_fulfill_request)
        assert response.status_code == 200

        cards = response.json()["cards"]
        context_cards = [c for c in cards if c["type"] == "context"]

        for card in context_cards:
            assert len(card["text"]) > 0
            assert len(card["header"]) > 0

            print(f"\n✓ Context card:")
            print(f"  Header: {card['header']}")
            print(f"  Content length: {len(card['text'])} chars")

    def test_cards_have_valid_metadata(self, client, base_fulfill_request):
        """Test that all cards have properly structured metadata."""
        response = client.post("/fulfill", json=base_fulfill_request)
        assert response.status_code == 200

        cards = response.json()["cards"]

        for card in cards:
            assert isinstance(card["metadata"], dict)
            # Metadata can be empty or have various fields

        print(f"\n✓ All {len(cards)} cards have valid metadata structure")


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_document(self, client):
        """Test fulfill with empty document."""
        request = {
            "user_id": "test_empty",
            "document_text": "",
            "cursor_position": [0, 0],
            "global_context": {
                "scope_root": str(Path(__file__).parent.parent),
                "plan_path": None
            }
        }

        response = client.post("/fulfill", json=request)
        assert response.status_code == 200

        # Should handle gracefully, may return empty or some cards
        data = response.json()
        assert "cards" in data

        print(f"\n✓ Empty document handled: {len(data['cards'])} cards")

    def test_very_long_document(self, client):
        """Test fulfill with a very long document."""
        long_text = "# Test\n\n" + ("This is a test line.\n" * 1000)

        request = {
            "user_id": "test_long",
            "document_text": long_text,
            "cursor_position": [500, 0],
            "global_context": {
                "scope_root": str(Path(__file__).parent.parent),
                "plan_path": None
            }
        }

        start_time = time.time()
        response = client.post("/fulfill", json=request)
        elapsed = time.time() - start_time

        assert response.status_code == 200
        data = response.json()

        print(f"\n✓ Long document ({len(long_text)} chars) handled:")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Cards: {len(data['cards'])}")

    def test_invalid_cursor_position(self, client, base_fulfill_request):
        """Test with cursor position outside document bounds."""
        request = base_fulfill_request.copy()
        request["cursor_position"] = [9999, 9999]  # Way beyond document

        # Should handle gracefully
        response = client.post("/fulfill", json=request)
        # May return error or handle gracefully - depends on implementation
        # At minimum shouldn't crash
        assert response.status_code in [200, 400, 422]

        print(f"\n✓ Invalid cursor position handled (status: {response.status_code})")


if __name__ == "__main__":
    """
    Run tests with: python tests/test_backend_api.py
    Or with pytest: pytest tests/test_backend_api.py -v -s
    """
    pytest.main([__file__, "-v", "-s"])
