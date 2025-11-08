"""
Detailed benchmarking script for individual fulfillers.

This script tests each fulfiller in isolation with REAL LLM calls
and provides detailed performance metrics.

Run with: python tests/benchmark_fulfillers.py
"""

import asyncio
import time
import statistics
from pathlib import Path
from typing import List, Dict, Any

from shared.models import Card, CardType
from shared.context import GlobalPreferenceContext
from parallizer.fulfillers.completions.completions import Completions
from parallizer.fulfillers.ambiguities.ambiguities import Ambiguities
from parallizer.fulfillers.web_context.web_context import WebContext
from parallizer.fulfillers.codesearch.search import CodeSearch


# Test document
TEST_DOCUMENT = Path(__file__).parent / "fixtures" / "test_document.md"


class FulfillerBenchmark:
    """Benchmark runner for individual fulfillers."""

    def __init__(self, num_runs: int = 3):
        self.num_runs = num_runs
        self.test_document = self._load_test_document()
        self.global_context = GlobalPreferenceContext(
            scope_root=str(Path(__file__).parent.parent),
            plan_path=None
        )

    def _load_test_document(self) -> str:
        """Load the test document."""
        if not TEST_DOCUMENT.exists():
            raise FileNotFoundError(f"Test document not found: {TEST_DOCUMENT}")
        return TEST_DOCUMENT.read_text()

    async def benchmark_fulfiller(
        self,
        fulfiller_name: str,
        fulfiller,
        cursor_position: tuple = (10, 0)
    ) -> Dict[str, Any]:
        """
        Benchmark a single fulfiller.

        Args:
            fulfiller_name: Name of the fulfiller for display
            fulfiller: Fulfiller instance
            cursor_position: Cursor position (line, col)

        Returns:
            Dictionary with benchmark results
        """
        print(f"\n{'='*70}")
        print(f"Benchmarking: {fulfiller_name}")
        print(f"{'='*70}")

        # Check availability first
        try:
            is_available = await fulfiller.is_available()
            print(f"Availability: {'✓ Available' if is_available else '✗ Not Available'}")

            if not is_available:
                return {
                    "name": fulfiller_name,
                    "available": False,
                    "error": "Fulfiller not available"
                }
        except Exception as e:
            print(f"Availability check failed: {e}")
            return {
                "name": fulfiller_name,
                "available": False,
                "error": str(e)
            }

        # Run benchmark
        timings = []
        card_counts = []
        errors = []

        for run in range(self.num_runs):
            print(f"\nRun {run + 1}/{self.num_runs}:")

            try:
                start_time = time.time()
                cards = await fulfiller.forward(
                    document_text=self.test_document,
                    cursor_position=cursor_position,
                    global_context=self.global_context
                )
                elapsed = time.time() - start_time

                timings.append(elapsed)
                card_counts.append(len(cards))

                print(f"  Time: {elapsed:.2f}s")
                print(f"  Cards returned: {len(cards)}")

                # Show card details
                for i, card in enumerate(cards, 1):
                    print(f"    {i}. [{card.type.value}] {card.header}")
                    if len(card.text) > 80:
                        print(f"       {card.text[:80]}...")
                    else:
                        print(f"       {card.text}")

            except Exception as e:
                print(f"  ✗ Error: {e}")
                errors.append(str(e))

        # Calculate statistics
        if timings:
            avg_time = statistics.mean(timings)
            min_time = min(timings)
            max_time = max(timings)
            std_dev = statistics.stdev(timings) if len(timings) > 1 else 0
            avg_cards = statistics.mean(card_counts)

            print(f"\n{'-'*70}")
            print(f"Statistics ({self.num_runs} runs):")
            print(f"  Average time: {avg_time:.2f}s (±{std_dev:.2f}s)")
            print(f"  Min time: {min_time:.2f}s")
            print(f"  Max time: {max_time:.2f}s")
            print(f"  Average cards: {avg_cards:.1f}")
            print(f"{'='*70}")

            return {
                "name": fulfiller_name,
                "available": True,
                "runs": self.num_runs,
                "avg_time": avg_time,
                "min_time": min_time,
                "max_time": max_time,
                "std_dev": std_dev,
                "avg_cards": avg_cards,
                "all_timings": timings,
                "all_card_counts": card_counts,
                "errors": errors
            }
        else:
            return {
                "name": fulfiller_name,
                "available": True,
                "runs": 0,
                "errors": errors
            }

    async def run_all_benchmarks(self) -> List[Dict[str, Any]]:
        """Run benchmarks for all fulfillers."""
        print("\n" + "="*70)
        print("PARALLIZER FULFILLER BENCHMARKS")
        print("="*70)
        print(f"Test document: {TEST_DOCUMENT}")
        print(f"Document size: {len(self.test_document)} characters")
        print(f"Runs per fulfiller: {self.num_runs}")
        print(f"Scope root: {self.global_context.scope_root}")

        results = []

        # 1. Completions Fulfiller
        try:
            completions = Completions()
            result = await self.benchmark_fulfiller(
                "Completions (Inline Code Completion)",
                completions,
                cursor_position=(15, 20)  # In the middle of code
            )
            results.append(result)
        except Exception as e:
            print(f"\n✗ Failed to initialize Completions: {e}")
            results.append({
                "name": "Completions",
                "available": False,
                "error": str(e)
            })

        # 2. Ambiguities Fulfiller
        try:
            ambiguities = Ambiguities()
            result = await self.benchmark_fulfiller(
                "Ambiguities (Question Detection)",
                ambiguities,
                cursor_position=(20, 0)  # At questions section
            )
            results.append(result)
        except Exception as e:
            print(f"\n✗ Failed to initialize Ambiguities: {e}")
            results.append({
                "name": "Ambiguities",
                "available": False,
                "error": str(e)
            })

        # 3. WebContext Fulfiller
        try:
            web_context = WebContext()
            result = await self.benchmark_fulfiller(
                "WebContext (Web Search)",
                web_context,
                cursor_position=(5, 0)  # At introduction
            )
            results.append(result)
        except Exception as e:
            print(f"\n✗ Failed to initialize WebContext: {e}")
            results.append({
                "name": "WebContext",
                "available": False,
                "error": str(e)
            })

        # 4. CodeSearch Fulfiller
        try:
            code_search = CodeSearch()
            result = await self.benchmark_fulfiller(
                "CodeSearch (Ripgrep)",
                code_search,
                cursor_position=(10, 0)
            )
            results.append(result)
        except Exception as e:
            print(f"\n✗ Failed to initialize CodeSearch: {e}")
            results.append({
                "name": "CodeSearch",
                "available": False,
                "error": str(e)
            })

        return results

    def print_summary(self, results: List[Dict[str, Any]]):
        """Print a summary comparison of all fulfillers."""
        print("\n" + "="*70)
        print("SUMMARY - ALL FULFILLERS")
        print("="*70)

        # Table header
        print(f"\n{'Fulfiller':<30} {'Status':<12} {'Avg Time':<12} {'Cards':<10}")
        print("-" * 70)

        # Sort by average time
        available_results = [r for r in results if r.get("available") and "avg_time" in r]
        unavailable_results = [r for r in results if not r.get("available") or "avg_time" not in r]

        available_results.sort(key=lambda x: x.get("avg_time", float('inf')))

        # Print available fulfillers
        for result in available_results:
            name = result["name"]
            status = "✓ Available"
            avg_time = f"{result['avg_time']:.2f}s"
            avg_cards = f"{result['avg_cards']:.1f}"

            print(f"{name:<30} {status:<12} {avg_time:<12} {avg_cards:<10}")

        # Print unavailable fulfillers
        for result in unavailable_results:
            name = result["name"]
            status = "✗ Unavailable"
            error = result.get("error", "Unknown error")

            print(f"{name:<30} {status:<12} {error[:30]:<12}")

        # Overall statistics
        if available_results:
            total_avg_time = sum(r["avg_time"] for r in available_results)
            fastest = min(available_results, key=lambda x: x["avg_time"])
            slowest = max(available_results, key=lambda x: x["avg_time"])

            print("\n" + "-" * 70)
            print(f"Fastest: {fastest['name']} ({fastest['avg_time']:.2f}s)")
            print(f"Slowest: {slowest['name']} ({slowest['avg_time']:.2f}s)")
            print(f"Total time (all fulfillers): {total_avg_time:.2f}s")
            print(f"Available: {len(available_results)}/{len(results)}")

        print("=" * 70)


async def main():
    """Main benchmark entry point."""
    benchmark = FulfillerBenchmark(num_runs=3)

    try:
        results = await benchmark.run_all_benchmarks()
        benchmark.print_summary(results)

        # Save results to JSON
        import json
        output_file = Path(__file__).parent / "benchmark_results.json"

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n✓ Results saved to: {output_file}")

    except KeyboardInterrupt:
        print("\n\n✗ Benchmark interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
