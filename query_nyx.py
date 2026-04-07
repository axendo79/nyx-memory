"""
query_nyx.py — search Nyx memory from the command line.

Usage:
    python query_nyx.py <search term>
    python query_nyx.py "project ideas"
"""

import os
import sys
from dotenv import load_dotenv
from memory.store import load_memories
from memory.retrieve import retrieve_relevant

load_dotenv()

MEMORY_PATH = os.path.join(os.path.dirname(__file__), "data", "memory.json")
MIN_SCORE = float(os.getenv("MIN_SCORE", 0.3))


def main():
    if len(sys.argv) < 2:
        print("Usage: python query_nyx.py <search term>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    memories = load_memories(MEMORY_PATH)

    if not memories:
        print("Memory is empty.")
        sys.exit(0)

    results = retrieve_relevant(query, memories, top_n=10, min_score=MIN_SCORE)

    if not results:
        print(f"No memories found for: {query!r}")
        sys.exit(0)

    print(f"Query: {query!r}  —  {len(results)} result(s)\n")
    for i, m in enumerate(results, 1):
        score = m.get("score", 0)
        text = m.get("text", "")
        print(f"  {i}. [score: {score:.2f}]  {text}")

    print()


if __name__ == "__main__":
    main()
