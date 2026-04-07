"""
Memory store — handles persistence and scoring.
JSON-backed. No external database.
"""

import json
import os
import time
from typing import List, Dict


def load_memories(path: str) -> List[Dict]:
    """Load memories from JSON file. Returns empty list if file missing."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_memories(path: str, memories: List[Dict]) -> None:
    """Save memories to JSON file. Creates directory if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memories, f, indent=2, ensure_ascii=False)


def add_memory(memories: List[Dict], user_input: str, response: str) -> List[Dict]:
    """
    Add a new memory entry from the current exchange.
    Score starts at 1.0. Decays over time if not retrieved.
    """
    entry = {
        "text": f"User said: {user_input} | Nyx responded: {response[:200]}",
        "score": 1.0,
        "last_used": time.time(),
        "created": time.time(),
    }
    memories.append(entry)
    return memories


def boost_score(memory: Dict, amount: float = 0.5) -> Dict:
    """
    Increase score when memory is retrieved.
    TODO: Refine scoring to reflect confirmed usefulness, not just retrieval.
    """
    memory["score"] = min(memory["score"] + amount, 10.0)  # Cap at 10
    memory["last_used"] = time.time()
    return memory


def apply_decay(memories: List[Dict], decay_rate: float = 0.99, min_score: float = 0.3) -> List[Dict]:
    """
    Apply score decay to all memories.
    Prune entries that fall below min_score threshold.
    Call this periodically (e.g., on startup or after N interactions).
    """
    decayed = []
    for m in memories:
        m["score"] *= decay_rate
        if m["score"] >= min_score:
            decayed.append(m)
    return decayed
