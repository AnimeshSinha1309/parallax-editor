#!/usr/bin/env python3
"""
Benchmark script comparing Google Search (Gemini Flash 2.5) vs Perplexity Search.

This script tests both search implementations with a variety of queries and
compares their performance, quality, and citation accuracy.
"""

import asyncio
import time
import json
from typing import List, Dict, Any
from datetime import datetime
import sys
import os

# Add parallizer to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'parallizer'))

from parallizer.utils.google_search import GoogleSearch, SearchResponse as GoogleResponse
from parallizer.utils.perplexity import PerplexitySearch, SearchResponse as PerplexityResponse


class SearchBenchmark:
    """Benchmark tool for comparing search implementations."""

    def __init__(self):
        """Initialize both search clients."""
        try:
            self.google = GoogleSearch()
            self.google_available = True
        except ValueError as e:
            print(f"⚠️  Google Search not available: {e}")
            self.google_available = False

        try:
            self.perplexity = PerplexitySearch()
            self.perplexity_available = True
        except ValueError as e:
            print(f"⚠️  Perplexity Search not available: {e}")
            self.perplexity_available = False

        if not self.google_available and not self.perplexity_available:
            raise RuntimeError("Neither Google nor Perplexity search is available!")

    async def benchmark_query(
        self,
        query: str,
        service: str
    ) -> Dict[str, Any]:
        """
        Benchmark a single query on a service.

        Args:
            query: The search query
            service: Either 'google' or 'perplexity'

        Returns:
            Dict with timing, result, and metadata
        """
        start_time = time.time()

        if service == "google" and self.google_available:
            result = await self.google.search(query)
        elif service == "perplexity" and self.perplexity_available:
            result = await self.perplexity.search(query)
        else:
            return {
                "error": f"{service} not available",
                "latency": 0,
                "success": False
            }

        latency = time.time() - start_time

        return {
            "query": query,
            "service": service,
            "success": result.success,
            "latency": latency,
            "content_length": len(result.content) if result.success else 0,
            "num_citations": len(result.citations) if result.success else 0,
            "citations": result.citations if result.success else [],
            "content": result.content if result.success else "",
            "error": result.error if not result.success else None
        }

    async def run_parallel_comparison(
        self,
        queries: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run queries in parallel on both services.

        Args:
            queries: List of search queries to test

        Returns:
            Dict with results for each service
        """
        print(f"\n🚀 Running {len(queries)} queries on both services in parallel...\n")

        # Create tasks for all queries on both services
        tasks = []
        for query in queries:
            if self.google_available:
                tasks.append(self.benchmark_query(query, "google"))
            if self.perplexity_available:
                tasks.append(self.benchmark_query(query, "perplexity"))

        # Run all tasks in parallel
        results = await asyncio.gather(*tasks)

        # Group results by service
        google_results = [r for r in results if r.get("service") == "google"]
        perplexity_results = [r for r in results if r.get("service") == "perplexity"]

        return {
            "google": google_results,
            "perplexity": perplexity_results
        }

    def print_comparison(self, results: Dict[str, List[Dict[str, Any]]]):
        """Print a formatted comparison of results."""
        google_results = results.get("google", [])
        perplexity_results = results.get("perplexity", [])

        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS")
        print("=" * 80)

        # Overall statistics
        print("\n📊 OVERALL STATISTICS\n")

        for service_name, service_results in [("Google Gemini", google_results), ("Perplexity", perplexity_results)]:
            if not service_results:
                print(f"{service_name}: Not available")
                continue

            successful = [r for r in service_results if r["success"]]
            failed = [r for r in service_results if not r["success"]]

            avg_latency = sum(r["latency"] for r in successful) / len(successful) if successful else 0
            avg_content_length = sum(r["content_length"] for r in successful) / len(successful) if successful else 0
            avg_citations = sum(r["num_citations"] for r in successful) / len(successful) if successful else 0
            total_citations = sum(r["num_citations"] for r in successful)

            print(f"\n{service_name}:")
            print(f"  Success rate: {len(successful)}/{len(service_results)} ({len(successful)/len(service_results)*100:.1f}%)")
            print(f"  Avg latency: {avg_latency:.2f}s")
            print(f"  Avg content length: {avg_content_length:.0f} chars")
            print(f"  Avg citations per query: {avg_citations:.1f}")
            print(f"  Total citations: {total_citations}")

            if failed:
                print(f"  Failed queries: {len(failed)}")
                for fail in failed:
                    print(f"    - {fail['query'][:50]}...: {fail['error']}")

        # Query-by-query comparison
        print("\n" + "=" * 80)
        print("QUERY-BY-QUERY COMPARISON")
        print("=" * 80)

        num_queries = max(len(google_results), len(perplexity_results))
        for i in range(num_queries):
            google_result = google_results[i] if i < len(google_results) else None
            perplexity_result = perplexity_results[i] if i < len(perplexity_results) else None

            if google_result:
                query = google_result["query"]
            elif perplexity_result:
                query = perplexity_result["query"]
            else:
                continue

            print(f"\n{'─' * 80}")
            print(f"Query: {query}")
            print(f"{'─' * 80}")

            # Google results
            if google_result:
                print(f"\n🔵 Google Gemini Flash 2.5:")
                if google_result["success"]:
                    print(f"  ⏱️  Latency: {google_result['latency']:.2f}s")
                    print(f"  📝 Content length: {google_result['content_length']} chars")
                    print(f"  🔗 Citations: {google_result['num_citations']}")
                    print(f"\n  Content preview:")
                    preview = google_result['content'][:300] + "..." if len(google_result['content']) > 300 else google_result['content']
                    print(f"  {preview}")
                    if google_result['citations']:
                        print(f"\n  Citations:")
                        for idx, citation in enumerate(google_result['citations'][:5], 1):
                            print(f"    [{idx}] {citation}")
                        if len(google_result['citations']) > 5:
                            print(f"    ... and {len(google_result['citations']) - 5} more")
                else:
                    print(f"  ❌ Error: {google_result['error']}")

            # Perplexity results
            if perplexity_result:
                print(f"\n🟣 Perplexity:")
                if perplexity_result["success"]:
                    print(f"  ⏱️  Latency: {perplexity_result['latency']:.2f}s")
                    print(f"  📝 Content length: {perplexity_result['content_length']} chars")
                    print(f"  🔗 Citations: {perplexity_result['num_citations']}")
                    print(f"\n  Content preview:")
                    preview = perplexity_result['content'][:300] + "..." if len(perplexity_result['content']) > 300 else perplexity_result['content']
                    print(f"  {preview}")
                    if perplexity_result['citations']:
                        print(f"\n  Citations:")
                        for idx, citation in enumerate(perplexity_result['citations'][:5], 1):
                            print(f"    [{idx}] {citation}")
                        if len(perplexity_result['citations']) > 5:
                            print(f"    ... and {len(perplexity_result['citations']) - 5} more")
                else:
                    print(f"  ❌ Error: {perplexity_result['error']}")

            # Speed comparison
            if google_result and perplexity_result and google_result["success"] and perplexity_result["success"]:
                google_latency = google_result["latency"]
                perplexity_latency = perplexity_result["latency"]
                if google_latency < perplexity_latency:
                    speedup = (perplexity_latency / google_latency - 1) * 100
                    print(f"\n  ⚡ Google was {speedup:.1f}% faster")
                else:
                    speedup = (google_latency / perplexity_latency - 1) * 100
                    print(f"\n  ⚡ Perplexity was {speedup:.1f}% faster")

        print("\n" + "=" * 80)

    async def run_benchmark(self, queries: List[str]):
        """Run the full benchmark suite."""
        print("=" * 80)
        print("SEARCH API BENCHMARK: Google Gemini vs Perplexity")
        print("=" * 80)
        print(f"\nTimestamp: {datetime.now().isoformat()}")
        print(f"Queries: {len(queries)}")

        # Check availability
        print("\n📡 Checking API availability...")
        if self.google_available:
            try:
                google_status = await self.google.is_available()
                print(f"  Google Gemini: {'✅ Available' if google_status else '❌ Unavailable'}")
                if not google_status:
                    self.google_available = False
            except Exception as e:
                print(f"  Google Gemini: ❌ Error checking availability: {str(e)[:50]}")
                self.google_available = False

        if self.perplexity_available:
            try:
                perplexity_status = await self.perplexity.is_available()
                print(f"  Perplexity: {'✅ Available' if perplexity_status else '❌ Unavailable'}")
                if not perplexity_status:
                    self.perplexity_available = False
            except Exception as e:
                print(f"  Perplexity: ❌ Error checking availability: {str(e)[:50]}")
                self.perplexity_available = False

        # Check if at least one service is available
        if not self.google_available and not self.perplexity_available:
            print("\n❌ No search services available! Cannot run benchmark.")
            print("   Please check your API keys and network connection.")
            return

        # Run benchmarks
        results = await self.run_parallel_comparison(queries)

        # Print results
        self.print_comparison(results)

        # Save results to JSON
        output_file = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "queries": queries,
                "results": results
            }, f, indent=2)

        print(f"\n💾 Results saved to: {output_file}\n")

        # Cleanup
        if self.google_available:
            await self.google.close()
        if self.perplexity_available:
            await self.perplexity.close()


async def main():
    """Main entry point."""
    # Define test queries covering different types of searches
    test_queries = [
        # Current events
        "What are the latest developments in AI in 2025?",

        # Technical questions
        "How does Python asyncio work and what are best practices?",

        # Factual queries
        "Who won the 2024 UEFA European Championship?",

        # Complex queries
        "Compare the performance of Gemini 2.5 Flash vs GPT-4 for coding tasks",

        # Recent news
        "What are the current trends in web development frameworks?",

        # Scientific queries
        "What is the latest research on quantum computing applications?",

        # Comparative queries
        "Differences between React and Vue.js in 2025",

        # Specific technical query
        "Best practices for implementing OAuth 2.0 in Python web applications"
    ]

    benchmark = SearchBenchmark()
    await benchmark.run_benchmark(test_queries)


if __name__ == "__main__":
    asyncio.run(main())
