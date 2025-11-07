"""Test script for RipgrepContext functionality."""

import asyncio
from fulfillers.codesearch import CodeSearch, RipgrepContext, RipgrepContextError


async def test_auto_git_repo():
    """Test auto-discovery of current git repo."""
    print("Test 1: Auto-discover git repo")
    try:
        search = CodeSearch()
        result = await search.search("class RipgrepContext")
        print(f"✓ Found {result.total_matches} matches")
        if result.matches:
            print(f"  First match: {result.matches[0].file_path}:{result.matches[0].line_number}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def test_explicit_context():
    """Test explicit context with added path."""
    print("\nTest 2: Explicit context with added path")
    try:
        context = RipgrepContext(auto_add_current_repo=False)
        context.add_path("./fulfillers")
        search = CodeSearch(context=context)
        result = await search.search("class")
        print(f"✓ Found {result.total_matches} matches in ./fulfillers")
    except Exception as e:
        print(f"✗ Error: {e}")


async def test_add_git_repo():
    """Test adding git repo explicitly."""
    print("\nTest 3: Add git repo by path")
    try:
        context = RipgrepContext(auto_add_current_repo=False)
        context.add_git_repo(".")
        search = CodeSearch(context=context)
        result = await search.search("def search")
        print(f"✓ Found {result.total_matches} matches")
        if result.matches:
            print(f"  First match: {result.matches[0].file_path}:{result.matches[0].line_number}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def test_multiple_paths():
    """Test multiple paths in context."""
    print("\nTest 4: Multiple paths in context")
    try:
        context = RipgrepContext(auto_add_current_repo=False)
        context.add_path("./fulfillers/codesearch")
        context.add_path("./docs")
        print(f"  Context has {len(context)} paths")
        search = CodeSearch(context=context)
        result = await search.search("search")
        print(f"✓ Found {result.total_matches} matches across multiple paths")
    except Exception as e:
        print(f"✗ Error: {e}")


async def test_backwards_compatibility():
    """Test backwards compatibility with directory parameter."""
    print("\nTest 5: Backwards compatibility with directory parameter")
    try:
        search = CodeSearch()
        result = await search.search("class", directory="./fulfillers")
        print(f"✓ Found {result.total_matches} matches (backwards compatible)")
    except Exception as e:
        print(f"✗ Error: {e}")


async def test_error_no_git_repo():
    """Test error when no git repo found."""
    print("\nTest 6: Error handling - no git repo")
    try:
        context = RipgrepContext(auto_add_current_repo=False)
        context.add_git_repo("/tmp")
        print("✗ Should have raised an error")
    except RipgrepContextError as e:
        print(f"✓ Correctly raised error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


async def main():
    print("Testing RipgrepContext Implementation")
    print("=" * 50)

    # Check if ripgrep is available
    search = CodeSearch()
    if not await search.is_available():
        print("✗ ripgrep is not installed or not in PATH")
        return

    await test_auto_git_repo()
    await test_explicit_context()
    await test_add_git_repo()
    await test_multiple_paths()
    await test_backwards_compatibility()
    await test_error_no_git_repo()

    print("\n" + "=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
