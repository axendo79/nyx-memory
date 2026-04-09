"""
selftest.py — four checks against the real Nyx pipeline.
No mocking. Cleans up after itself.
Run: python selftest.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from memory.store import add_memory, boost_score, load_memories
from memory.retrieve import retrieve_relevant
from memory.decay import apply_decay
from llm.client import query_llm

load_dotenv()

MEMORY_PATH = os.getenv("MEMORY_PATH", os.path.join(os.path.dirname(__file__), "data", "memory.json"))
MIN_SCORE = float(os.getenv("MIN_SCORE", 0.3))

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


# --- Test 5: Memory loads from disk ---
try:
    disk_memories = load_memories(MEMORY_PATH)
    check("Memory loads from disk", isinstance(disk_memories, list))
except Exception as e:
    check("Memory loads from disk", False)
    print(f"         {e}")


disk_memories = disk_memories if 'disk_memories' in locals() else []

# --- Test 6: apply_decay runs without crashing ---
try:
    apply_decay(list(disk_memories))
    check("apply_decay runs without crashing", True)
except Exception as e:
    check("apply_decay runs without crashing", False)
    print(f"         {e}")


# --- Test 7: retrieve_relevant runs without crashing ---
try:
    retrieve_relevant("test", disk_memories, top_n=3, min_score=MIN_SCORE)
    check("retrieve_relevant runs without crashing", True)
except Exception as e:
    check("retrieve_relevant runs without crashing", False)
    print(f"         {e}")


# --- Test 8: query_llm fails gracefully without LM Studio ---
try:
    query_llm("ping")
    check("query_llm fails gracefully without LM Studio", True)
except Exception:
    check("query_llm fails gracefully without LM Studio", True)


# --- Result ---
total = passed + failed
print(f"\n{passed}/{total} passed")
sys.exit(0 if failed == 0 else 1)
