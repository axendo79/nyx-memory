import glob as _glob
import os
import re
from pathlib import Path
from typing import List, Dict

try:
    from bs4 import BeautifulSoup as _BeautifulSoup
    _BS4_AVAILABLE = True
except ImportError:
    _BS4_AVAILABLE = False

KNOWLEDGE_PATH = Path(os.getenv(
    "KNOWLEDGE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Knowledge"),
))

_SUPPORTED_EXTS = {".md", ".txt", ".html"}


def tokenize(text: str) -> set:
    return set(re.findall(r'\b\w+\b', text.lower()))


def read_knowledge_files() -> List[Dict]:
    docs = []
    files = [
        p for p in _glob.glob(str(KNOWLEDGE_PATH / "*"))
        if Path(p).suffix in _SUPPORTED_EXTS
    ]

    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            if path.endswith(".html") and _BS4_AVAILABLE:
                content = _BeautifulSoup(
                    content, "html.parser"
                ).get_text(separator=" ", strip=True)

            docs.append({
                "name": Path(path).name,
                "mtime": os.path.getmtime(path),
                "content": content,
            })
        except Exception:
            continue

    return docs


def retrieve_knowledge(query: str, top_n: int = 2) -> List[Dict]:
    query_words = tokenize(query)
    docs = read_knowledge_files()

    docs.sort(key=lambda d: d["mtime"], reverse=True)

    # 2 newest always inject, truncated to trailing content
    always_docs = docs[:2]
    for d in always_docs:
        d["content"] = d["content"][-3000:]

    scored_docs = []
    for doc in docs[2:]:
        words = tokenize(doc["content"])
        overlap = query_words & words
        min_overlap = 1 if len(query_words) < 4 else 2
        if len(overlap) < min_overlap:
            continue
        score = len(overlap) / max(len(query_words), 1)
        scored_docs.append((score, doc))

    scored_docs.sort(key=lambda x: x[0], reverse=True)
    top_scored = [doc for _, doc in scored_docs[:top_n]]

    return always_docs + top_scored
