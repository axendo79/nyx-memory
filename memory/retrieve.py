"""
Memory retrieval — keyword match with score threshold.
Simple and fast for V1. Embedding-based retrieval is a future upgrade.
"""

import re
from typing import List, Dict

from memory.store import boost_score
from nyx_logger import get_logger

log = get_logger("retrieve")


def retrieve_relevant(
    query: str,
    memories: List[Dict],
    top_n: int = 5,
    min_score: float = 0.3,
) -> List[Dict]:
    """
    Find memories relevant to the query using keyword matching.
    Only returns memories above min_score threshold.
    Boosts score of matched memories (retrieval-based scoring).
    Returns top_n results sorted by score descending.
    """
    query_words = set(re.findall(r'\b\w+\b', query.lower()))
    scored = []

    for memory in memories:
        if memory.get("score", 0) < min_score:
            continue

        memory_words = set(re.findall(r'\b\w+\b', memory["text"].lower()))
        overlap = query_words & memory_words

        if overlap:
            relevance = len(overlap) * memory["score"]
            scored.append((relevance, memory))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, memory in scored[:top_n]:
        memory = boost_score(memory)
        results.append(memory)

    top_score = results[0]["score"] if results else 0.0
    log.info(
        "retrieve event=retrieve_relevant query_len=%d candidates=%d results=%d top_score=%.2f",
        len(query_words), len(memories), len(results), top_score,
    )

    return results
