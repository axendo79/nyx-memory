"""
Memory retrieval — keyword match with score threshold.
Simple and fast for V1. Embedding-based retrieval is a future upgrade.
"""

from typing import List, Dict
from memory.store import boost_score


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
    query_words = set(query.lower().split())
    scored = []

    for memory in memories:
        if memory.get("score", 0) < min_score:
            continue

        memory_words = set(memory["text"].lower().split())
        overlap = query_words & memory_words

        if overlap:
            # Weight by keyword overlap + existing score
            relevance = len(overlap) * memory["score"]
            scored.append((relevance, memory))

    # Sort by relevance descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Boost scores of retrieved memories and return top N
    results = []
    for _, memory in scored[:top_n]:
        memory = boost_score(memory)
        results.append(memory)

    return results
