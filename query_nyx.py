import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent))

from memory.store import load_memories
from memory.retrieve import retrieve_relevant

MEMORY_PATH = str(Path(__file__).parent / "data" / "memory.json")
TOP_N = 5
MIN_SCORE = 0.0  # Show everything in query tool, no threshold filtering


def main():
    if len(sys.argv) < 2:
        print('Usage: python query_nyx.py "your query"')
        sys.exit(0)

    query = " ".join(sys.argv[1:])
    memories = load_memories(MEMORY_PATH)
    results = retrieve_relevant(query, memories, top_n=TOP_N, min_score=MIN_SCORE)

    if not results:
        print("No relevant memories found.")
        sys.exit(0)

    print(f"\n--- Results for: {query!r} ---")
    for m in results:
        print(f"[Score: {m['score']:.2f}] {m['text']}")
    print()


if __name__ == "__main__":
    main()
