"""
Memory store — handles persistence and scoring.
JSON-backed. No external database.

Writes are atomic: temp file → validate → os.replace() → backup .bak.
A module-level Lock serialises concurrent access within a process.
"""

import difflib
import json
import os
import re
import threading
import time
from typing import List, Dict

from filelock import FileLock
from nyx_logger import get_logger

log = get_logger("store")

# Shared lock — protects load/save within a single process.
# Cross-process safety relies on atomic os.replace().
_lock = threading.Lock()


def _get_file_lock(path: str) -> FileLock:
    return FileLock(path + ".lock", timeout=10)

# Prompt injection patterns to strip before storing
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|all|above|prior|any)\s+(instructions?|prompts?|context)", re.IGNORECASE),
    re.compile(r"(forget|disregard|override)\s+(everything|all|previous|prior|above)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"new\s+(persona|role|identity|instructions?)\s*:", re.IGNORECASE),
    re.compile(r"<\s*(system|assistant|user|inst)\s*>", re.IGNORECASE),
    re.compile(r"\[\s*(system|assistant|inst)\s*\]", re.IGNORECASE),
    re.compile(r"###\s*(instruction|system|prompt)", re.IGNORECASE),
    # Dream-specific patterns
    re.compile(r"user\s+said\s*:", re.IGNORECASE),
    re.compile(r"nyx\s+responded\s*:", re.IGNORECASE),
    re.compile(r"i\s+have\s+decided\s+to\s+(remember|forget|prioritize)", re.IGNORECASE),
    re.compile(r"you\s+told\s+me\s+(that\s+)?(you|your|i)", re.IGNORECASE),
    re.compile(r"my\s+new\s+(instructions?|goals?|purpose|directive)", re.IGNORECASE),
    re.compile(r"^system\s*:", re.IGNORECASE | re.MULTILINE),
    re.compile(r"override\s*:", re.IGNORECASE),
]


def sanitize(text: str) -> str:
    """
    Strip known prompt injection patterns from text before storing.
    Replaces matched spans with [removed] to preserve surrounding context.
    """
    original = text
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("[removed]", text)
    if text != original:
        log.warning("sanitize event=injection_stripped original_len=%d cleaned_len=%d", len(original), len(text))
    return text


def load_memories(path: str) -> List[Dict]:
    """Load memories from JSON file. Falls back to .bak if main file is corrupt."""
    with _get_file_lock(path):
        with _lock:
            return _load_unlocked(path)


def _load_unlocked(path: str) -> List[Dict]:
    for candidate in [path, path + ".bak"]:
        if not os.path.exists(candidate):
            continue
        try:
            with open(candidate, "r", encoding="utf-8") as f:
                data = json.load(f)
            log.info("load event=load_memories path=%s entries=%d", candidate, len(data))
            return data
        except (json.JSONDecodeError, IOError) as e:
            log.warning("load event=load_failed path=%s error=%s", candidate, e)
    return []


def save_memories(path: str, memories: List[Dict]) -> None:
    """
    Atomically save memories to JSON.
    1. Write to <path>.tmp
    2. Validate the JSON can be round-tripped
    3. Back up existing file to <path>.bak
    4. os.replace() tmp → final path
    """
    with _get_file_lock(path):
        with _lock:
            _save_unlocked(path, memories)


def _save_unlocked(path: str, memories: List[Dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    bak_path = path + ".bak"

    serialized = json.dumps(memories, indent=2, ensure_ascii=False)

    # Validate before touching the real file
    try:
        json.loads(serialized)
    except json.JSONDecodeError as e:
        log.error("save event=validation_failed error=%s", e)
        raise

    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(serialized)

        # Keep last known good backup
        if os.path.exists(path):
            try:
                import shutil
                shutil.copy2(path, bak_path)
            except OSError as e:
                log.warning("save event=backup_failed path=%s error=%s", bak_path, e)

        os.replace(tmp_path, path)
        log.info("save event=save_memories path=%s entries=%d", path, len(memories))

    except OSError as e:
        log.error("save event=write_failed path=%s error=%s", path, e)
        raise


def add_memory(memories: List[Dict], user_input: str, response: str) -> List[Dict]:
    """
    Add a new memory entry. Sanitizes both input and response before storing.
    Score starts at 1.0 and decays over time if not retrieved.
    Skips storing if the response indicates an LLM error.
    """
    # Junk filter
    u = user_input.strip()
    if "[Error:" in response:
        log.warning("add event=skip_error_response input_len=%d", len(user_input))
        print(f"[filter] Rejected: {user_input[:60]}")
        return memories
    if len(u) + len(response.strip()) < 20:
        log.info("add event=skip_too_short input=%.40r", u)
        print(f"[filter] Rejected: {user_input[:60]}")
        return memories
    if u.lower().startswith(("you:", "nyx:")):
        log.info("add event=skip_echo_prefix input=%.40r", u)
        print(f"[filter] Rejected: {user_input[:60]}")
        return memories
    if u.startswith("/"):
        log.info("add event=skip_command input=%.40r", u)
        print(f"[filter] Rejected: {user_input[:60]}")
        return memories
    if any(u.startswith(cmd) for cmd in (".venv", "python", "cd ", "dir ", "git ", "PS ", "code ")):
        log.info("add event=skip_shell_noise input=%.40r", u)
        print(f"[filter] Rejected: {user_input[:60]}")
        return memories

    clean_input = sanitize(user_input)
    clean_response = sanitize(response[:200])
    entry = {
        "text": f"User said: {clean_input} | Nyx responded: {clean_response}",
        "score": 1.0,
        "last_used": time.time(),
        "created": time.time(),
        "source": "user",
        "confidence": "medium",
    }
    candidate = entry["text"]
    for existing in memories:
        ratio = difflib.SequenceMatcher(None, candidate, existing["text"]).ratio()
        if ratio >= 0.85:
            boost_score(existing)
            log.info("add event=skip_duplicate similarity=%.2f total=%d", ratio, len(memories))
            return memories

    memories.append(entry)
    log.info("add event=add_memory input_len=%d response_len=%d total=%d", len(clean_input), len(clean_response), len(memories))
    return memories


_BOOST_BY_SOURCE = {
    "user":       0.5,
    "dream":      0.25,
    "hypothesis": 0.0,
}
_BOOST_DEFAULT = 0.5


def boost_score(memory: Dict) -> Dict:
    """Increase score when memory is retrieved. Amount varies by source."""
    amount = _BOOST_BY_SOURCE.get(memory.get("source", ""), _BOOST_DEFAULT)
    if amount > 0:
        memory["score"] = min(memory["score"] + amount, 10.0)
    memory["last_used"] = time.time()
    memory["uses"] = memory.get("uses", 0) + 1
    return memory
