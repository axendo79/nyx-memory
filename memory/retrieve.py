"""
Memory retrieval — keyword match with score threshold.
Simple and fast for V1. Embedding-based retrieval is a future upgrade.
"""

import re
from typing import List, Dict

from memory.store import boost_score
from nyx_logger import get_logger

log = get_logger("retrieve")


def tokenize(text: str) -> set:
    return set(re.findall(r'\b\w+\b', text.lower()))


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
    query_words = tokenize(query)
    scored = []

    for memory in memories:
        if memory.get("score", 0) < min_score:
            continue

        memory_words = tokenize(memory["text"])

        # Exact matches
        exact = query_words & memory_words

        # Partial matches — query word is substring of memory word or vice versa
        partial = set()
        for qw in query_words:
            if qw not in exact and len(qw) >= 3:
                for mw in memory_words:
                    if len(mw) >= 3 and (qw in mw or mw in qw):
                        partial.add(qw)
                        break

        matched = exact | partial
        if not matched:
            continue

        # Coverage: fraction of query words matched
        coverage = len(matched) / max(len(query_words), 1)

        # Partial matches worth half an exact match
        match_score = len(exact) + (len(partial) * 0.5)

        relevance = match_score * coverage * memory["score"]
        scored.append((relevance, memory))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, memory in scored[:top_n]:
        memory = boost_score(memory)
        print(f"[BOOST] score boosted to {memory['score']:.2f}")
        results.append(memory)

    top_score = results[0]["score"] if results else 0.0
    log.info(
        "retrieve event=retrieve_relevant query_len=%d candidates=%d results=%d top_score=%.2f",
        len(query_words), len(memories), len(results), top_score,
    )

    return results
