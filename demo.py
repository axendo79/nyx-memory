"""
demo.py — Scripted comparison: baseline vs naive vs Nyx.
No user input required. Runs all three modes through the same scenarios
and shows what each injects and how responses differ.
"""

import contextlib
import io
import time

from llm.client import query_llm
from memory.decay import apply_decay
from memory.retrieve import retrieve_relevant
from memory.store import add_memory

MIN_SCORE = 0.3
INJECT_THRESHOLD = 0.5

SCENARIOS = [
    ("State a preference",  "I prefer concise answers"),
    ("State another",       "I like sci-fi"),
    ("Unrelated query",     "what's 2+2"),
    ("Recall preferences",  "what do I prefer?"),
    ("Inject noise",        "the weather is nice today"),
    ("Recall again",        "what do I like?"),
]


def _naive_store(memories, user_input, response):
    """Store every exchange unconditionally — no filtering, no decay."""
    memories.append({
        "text": f"User said: {user_input} | Nyx responded: {response}",
        "score": 1.0,
        "last_used": time.time(),
        "created": time.time(),
        "source": "user",
        "confidence": "medium",
    })
    return memories


def _build_prompt(user_input, memories):
    if not memories:
        return f"User: {user_input}"
    block = "\n".join(f"- {m['text'][:100]}" for m in memories)
    return f"Relevant memory:\n{block}\n\nUser: {user_input}"


def _query(prompt):
    result = query_llm(prompt)
    return "[LLM unavailable]" if result.startswith("[Error") else result


def run_demo():
    naive_memories = []
    nyx_memories = []

    for label, user_input in SCENARIOS:
        print(f"\n{'=' * 54}")
        print(f"=== TEST: {label} ===")
        print(f"Input: {user_input!r}")
        print(f"{'=' * 54}")

        # --- BASELINE ---
        print("\n[BASELINE]")
        baseline_response = _query(f"User: {user_input}")
        print(f"Response: {baseline_response}")

        # --- NAIVE ---
        print("\n[NAIVE]")
        naive_hits = retrieve_relevant(user_input, naive_memories, top_n=5, min_score=0.0)
        print(f"Memories injected: {len(naive_hits)}")
        naive_response = _query(_build_prompt(user_input, naive_hits))
        print(f"Response: {naive_response}")
        naive_memories = _naive_store(naive_memories, user_input, naive_response)

        # --- NYX ---
        print("\n[NYX]")
        nyx_hits = retrieve_relevant(user_input, nyx_memories, top_n=3, min_score=MIN_SCORE)
        injected = [m for m in nyx_hits if m["score"] >= INJECT_THRESHOLD]
        filtered = len(nyx_hits) - len(injected)
        suffix = f" (filtered {filtered})" if filtered else ""
        print(f"Memories injected: {len(injected)}{suffix}")
        nyx_response = _query(_build_prompt(user_input, injected))
        print(f"Response: {nyx_response}")
        with contextlib.redirect_stdout(io.StringIO()):
            nyx_memories = add_memory(nyx_memories, user_input, nyx_response)
        nyx_memories = apply_decay(nyx_memories)


if __name__ == "__main__":
    run_demo()
