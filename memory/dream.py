"""
Dream Cycle — synthesizes new memories from top existing ones.
Manual trigger only: /dream
Output stored with source: dream, confidence: low, score: 2.0
"""

import time
from typing import List, Dict

from llm.client import query_llm
from memory.store import save_memories
from nyx_logger import get_logger

log = get_logger("dream")


def run_dream(memories: List[Dict], memory_path: str) -> List[Dict]:
    # Select top 10 by score * recency weight, skip low-confidence
    def rank(m: Dict) -> float:
        age = time.time() - m.get("last_used", 0)
        recency = 1 / (1 + age / 86400)  # decay over days
        return m.get("score", 0) * recency

    candidates = sorted(memories, key=rank, reverse=True)[:10]

    memory_texts = [
        m["text"] for m in candidates
        if m.get("confidence", "medium") != "low"
    ]

    if not memory_texts:
        print("[dream] Not enough high-confidence memories to synthesize.")
        return memories

    block = "\n".join(f"- {t[:120]}" for t in memory_texts)
    prompt = (
        "You are reviewing your own memory. Based only on the entries below, "
        "write one concise insight or connection you notice. "
        "Do not repeat the entries. Do not invent facts. Be specific.\n\n"
        f"{block}"
    )

    print("[dream] Synthesizing...")
    result = query_llm(prompt)

    if not result or "[Error:" in result:
        print("[dream] Synthesis failed.")
        log.warning("dream event=synthesis_failed")
        return memories

    entry = {
        "text": result,
        "score": 0.8,
        "last_used": time.time(),
        "created": time.time(),
        "source": "dream",
        "confidence": "low",
        "uses": 0,
    }
    memories.append(entry)
    save_memories(memory_path, memories)

    print(f"[dream] Stored: {result}")
    print(f"[dream] 1 synthesis added.")
    log.info("dream event=stored result_len=%d total=%d", len(result), len(memories))

    return memories
