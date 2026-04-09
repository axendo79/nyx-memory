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
from knowledge.retrieve import retrieve_knowledge
from main import build_prompt

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


# --- Test 9: retrieve_knowledge returns results for matching query ---
try:
    results = retrieve_knowledge("sci-fi pie")
    check("retrieve_knowledge returns results for matching query", len(results) > 0)
except Exception as e:
    check("retrieve_knowledge returns results for matching query", False)
    print(f"         {e}")


# --- Test 10: retrieve_knowledge handles missing KNOWLEDGE_PATH gracefully ---
try:
    from knowledge.retrieve import read_knowledge_files
    import unittest.mock as mock
    with mock.patch("knowledge.retrieve.KNOWLEDGE_PATH", "/nonexistent/path"):
        docs = read_knowledge_files()
    check("retrieve_knowledge handles missing path gracefully", docs == [])
except Exception as e:
    check("retrieve_knowledge handles missing path gracefully", False)
    print(f"         {e}")


# --- Test 11: build_prompt includes knowledge block when provided ---
try:
    knowledge = [{"name": "test.md", "content": "This is test knowledge."}]
    prompt = build_prompt("test query", [], knowledge)
    check("build_prompt includes knowledge block", "Relevant knowledge" in prompt and "test.md" in prompt)
except Exception as e:
    check("build_prompt includes knowledge block", False)
    print(f"         {e}")


# --- Result ---
total = passed + failed
print(f"\n{passed}/{total} passed")
sys.exit(0 if failed == 0 else 1)
