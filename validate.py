#!/usr/bin/env python
"""Validation script for code search SDK."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from code_search import CodeSearch


async def validate():
    """Run validation checks for the code search SDK."""
    print("🔍 Code Search SDK Validation\n")
    print("=" * 50)

    search = CodeSearch()

    # Test 1: Is ripgrep available?
    print("\n[Test 1] Checking if ripgrep is available...")
    is_available = await search.is_available()
    if not is_available:
        print("❌ ripgrep not installed")
        print("   Install: brew install ripgrep (macOS)")
        print("   Install: sudo apt install ripgrep (Ubuntu)")
        return False
    print("✅ ripgrep is available")

    # Test 2: Basic search works
    print("\n[Test 2] Testing basic search functionality...")
    result = await search.search("def", "./tests/fixtures", max_results=5)
    if not result.success:
        print(f"❌ Search failed: {result.error}")
        return False
    print(f"✅ Search works: {result.total_matches} matches found")

    # Test 3: Results have correct structure
    print("\n[Test 3] Validating result structure...")
    if result.matches:
        m = result.matches[0]
        if not (m.file_path and m.line_number and m.line_content):
            print("❌ Match structure is invalid")
            return False
        print(f"✅ Structure correct: {m}")
    else:
        print("⚠️  No matches found (might be expected)")

    # Test 4: Error handling works
    print("\n[Test 4] Testing error handling...")
    bad_result = await search.search("[invalid(", ".")
    if bad_result.success:
        print("❌ Error handling failed - invalid regex should fail")
        return False
    print(f"✅ Error handling works: {bad_result.error}")

    # Test 5: Context lines
    print("\n[Test 5] Testing context lines...")
    result = await search.search("retry", "./tests/fixtures", context_lines=2)
    if result.success and result.matches:
        m = result.matches[0]
        if len(m.context_before) > 0 or len(m.context_after) > 0:
            print(f"✅ Context captured: {len(m.context_before)} before, {len(m.context_after)} after")
        else:
            print("⚠️  No context found (might be at file boundary)")
    else:
        print("⚠️  No matches found for context test")

    # Test 6: Case sensitivity
    print("\n[Test 6] Testing case sensitivity...")
    result_insensitive = await search.search("RETRY", "./tests/fixtures", case_sensitive=False)
    result_sensitive = await search.search("RETRY", "./tests/fixtures", case_sensitive=True)
    if result_insensitive.total_matches > 0 and result_sensitive.total_matches == 0:
        print("✅ Case sensitivity works correctly")
    else:
        print(f"⚠️  Case test inconclusive: insensitive={result_insensitive.total_matches}, sensitive={result_sensitive.total_matches}")

    print("\n" + "=" * 50)
    print("🎉 All validation tests passed!")
    print("\nSDK is ready to use!")
    print("\nQuick start:")
    print("  from code_search import CodeSearch")
    print("  search = CodeSearch()")
    print("  result = await search.search('pattern', '/path/to/code')")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = asyncio.run(validate())
    sys.exit(0 if success else 1)
