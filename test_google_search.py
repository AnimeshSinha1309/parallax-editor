#!/usr/bin/env python3
"""Quick test script for Google Search implementation."""

import asyncio
import sys
import os
import importlib.util

# Load google_search module directly to avoid __init__ issues
spec = importlib.util.spec_from_file_location(
    "google_search",
    os.path.join(os.path.dirname(__file__), 'parallizer/utils/google_search.py')
)
google_search_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(google_search_module)
GoogleSearch = google_search_module.GoogleSearch


async def main():
    """Test Google Search with a simple query."""
    print("Testing Google Search implementation...")
    print("=" * 60)

    try:
        searcher = GoogleSearch()
        print("✅ GoogleSearch initialized successfully")
        print(f"   Model: {searcher.model}")
        print(f"   API Key: {searcher.api_key[:10]}...")

        # Check availability
        print("\n📡 Checking API availability...")
        try:
            available = await searcher.is_available()
            print(f"   API Available: {'✅ Yes' if available else '❌ No'}")
        except Exception as e:
            print(f"   API Available: ❌ No (Error: {e})")
            available = False

        # Always try the query, even if availability check failed
        # Run a test query
        test_query = "Who won Euro 2024?"
        print(f"\n🔍 Testing query: '{test_query}'")
        print("   Waiting for response...")

        result = await searcher.search(test_query)

        print("\n📋 Results:")
        print(f"   Success: {result.success}")

        if result.success:
            print(f"   Content length: {len(result.content)} chars")
            print(f"   Number of citations: {len(result.citations)}")
            print(f"\n📝 Content:")
            print("   " + "─" * 56)
            print(f"   {result.content}")
            print("   " + "─" * 56)

            if result.citations:
                print(f"\n🔗 Citations ({len(result.citations)}):")
                for i, citation in enumerate(result.citations, 1):
                    print(f"   [{i}] {citation}")
        else:
            print(f"   Error: {result.error}")

        # Cleanup
        await searcher.close()
        print("\n✅ Test completed!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
