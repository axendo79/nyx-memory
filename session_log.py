"""
session_log.py — per-session structured decision log.
Records what Nyx decided to store, retrieve, and synthesize.

Separate from nyx_logger.py — no internal math, no debug events.
Log decisions only. Schema is stable; fields may be sparsely populated
until upstream modules surface the data.
"""

import json
import os
import time


class SessionLog:
    def __init__(self):
        os.makedirs("logs", exist_ok=True)
        self._started = int(time.time())
        self._path = os.path.join("logs", f"session_{self._started}.json")
        self._events = []

    def log(self, **kwargs) -> None:
        if "event" not in kwargs:
            raise ValueError("SessionLog.log() requires an 'event' key")
        kwargs["ts"] = time.time()
        self._events.append(kwargs)

    def log_ingest(self, stored: bool, near_miss: bool = False, text: str = "") -> None:
        self.log(
            event="ingest",
            stored=stored,
            near_miss=near_miss,
            text_preview=text[:80],
        )

    def log_retrieval(self, query: str, found: int, top_score: float) -> None:
        self.log(
            event="retrieval",
            query_preview=query[:80],
            found=found,
            top_score=round(top_score, 3),
        )

    def log_dream(self, success: bool, result_len: int = 0) -> None:
        self.log(
            event="dream",
            success=success,
            result_len=result_len,
        )

    def finalize(self) -> None:
        ingest_events = [e for e in self._events if e["event"] == "ingest"]
        dream_events  = [e for e in self._events if e["event"] == "dream"]
        summary = {
            "memories_added":    sum(1 for e in ingest_events if e.get("stored")),
            "memories_rejected": sum(1 for e in ingest_events if not e.get("stored")),
            "near_misses":       sum(1 for e in ingest_events if e.get("near_miss")),
            "consolidations":    len(dream_events),
        }
        payload = {
            "session_start": self._started,
            "session_end":   int(time.time()),
            "summary":       summary,
            "events":        self._events,
        }
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
