import os
import re
from typing import List, Dict

KNOWLEDGE_PATH = os.getenv(
    "KNOWLEDGE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Knowledge"),
)


def tokenize(text: str) -> set:
    return set(re.findall(r'\b\w+\b', text.lower()))


def read_knowledge_files() -> List[Dict]:
    docs = []
    if not os.path.exists(KNOWLEDGE_PATH):
        return docs

    for fname in os.listdir(KNOWLEDGE_PATH):
        if not fname.endswith(".md"):
            continue

        path = os.path.join(KNOWLEDGE_PATH, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                docs.append({
                    "name": fname,
                    "content": content,
                })
        except Exception:
            continue

    return docs


def retrieve_knowledge(query: str, top_n: int = 2) -> List[Dict]:
    query_words = tokenize(query)
    docs = read_knowledge_files()

    scored = []

    for doc in docs:
        words = tokenize(doc["content"])
        overlap = query_words & words

        if len(overlap) < 2:
            continue

        score = len(overlap) / max(len(query_words), 1)
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [doc for _, doc in scored[:top_n]]
