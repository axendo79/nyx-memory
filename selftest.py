"""
selftest.py — four checks against the real Nyx pipeline.
No mocking. Cleans up after itself.
Run: python selftest.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from memory.store import add_memory, boost_score
from memory.retrieve import retrieve_relevant

passed = 0
failed = 0


def check(name: str, result: bool) -> None:
    global passed, failed
    if result:
        print(f"  PASS  {name}")
        passed += 1
    else:
        print(f"  FAIL  {name}")
        failed += 1


# --- Test 1: Memory write + retrieve ---
memories = []
memories = add_memory(memories, "selftest write check", "write confirmed")
check(
    "Memory write + retrieve",
    len(memories) == 1 and "selftest write check" in memories[0]["text"]
)
memories = []  # cleanup


# --- Test 2: Retrieval (pie) ---
memories = []
memories = add_memory(memories, "what do you know about key lime pie", "It is a tart dessert")
results = retrieve_relevant("pie", memories, top_n=5, min_score=0.0)
check(
    "Retrieval matches 'pie' query",
    len(results) > 0 and any("pie" in r["text"].lower() for r in results)
)
memories = []  # cleanup


# --- Test 3: Dedup ---
memories = []
memories = add_memory(memories, "dedup test entry one", "response alpha")
score_before = memories[0]["score"]
memories = add_memory(memories, "dedup test entry one", "response alpha")
check(
    "Dedup — duplicate boosts score instead of adding entry",
    len(memories) == 1 and memories[0]["score"] > score_before
)
memories = []  # cleanup


# --- Test 4: Junk filter ---
memories = []
memories = add_memory(memories, "You: hello there", "should be filtered")
memories = add_memory(memories, "/debug something", "should be filtered")
memories = add_memory(memories, "cd D:\\Nyx", "should be filtered")
check(
    "Junk filter — echo/command/shell inputs not stored",
    len(memories) == 0
)
memories = []  # cleanup


# --- Result ---
total = passed + failed
print(f"\n{passed}/{total} passed")
sys.exit(0 if failed == 0 else 1)
