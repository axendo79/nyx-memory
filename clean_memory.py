"""
clean_memory.py — one-time cleanup of the memory store.

Removes entries where:
  - text contains "[Error:"
  - text is under 20 characters
  - user_input portion starts with a shell command prefix, slash command, or echo prefix

Deduplicates near-identical entries (>=85% similarity), keeping highest-scoring copy.

Creates a timestamped backup before writing the cleaned result.
"""

import difflib
import json
import os
import shutil
import time
from dotenv import load_dotenv

load_dotenv()

MEMORY_PATH = os.getenv(
    "MEMORY_PATH",
    os.path.join(os.path.dirname(__file__), "data", "memory.json"),
)


def load(path: str) -> list:
    if not os.path.exists(path):
        print(f"No memory file found at {path} — nothing to clean.")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save(path: str, memories: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(memories, f, indent=2, ensure_ascii=False)
    json.loads(open(tmp, encoding="utf-8").read())  # validate
    os.replace(tmp, path)


def dedup_memories(memories: list) -> list:
    kept = []
    for candidate in memories:
        duplicate_found = False
        for existing in kept:
            ratio = difflib.SequenceMatcher(
                None,
                candidate["text"],
                existing["text"]
            ).ratio()
            if ratio >= 0.85:
                if candidate["score"] > existing["score"]:
                    existing["text"] = candidate["text"]
                    existing["score"] = candidate["score"]
                duplicate_found = True
                break
        if not duplicate_found:
            kept.append(candidate)
    return kept


def main():
    memories = load(MEMORY_PATH)
    if not memories:
        return

    # Backup before touching anything
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak_path = MEMORY_PATH + f".{ts}.bak"
    shutil.copy2(MEMORY_PATH, bak_path)
    print(f"Backup saved: {bak_path}")

    _SHELL_PREFIXES = (".venv", "python", "cd ", "dir ", "git ", "PS ", "code ")

    def is_clean(m: dict) -> bool:
        text = m.get("text", "")
        if "[Error:" in text or len(text) < 20:
            return False
        if text.startswith("User said: "):
            user_part = text[len("User said: "):].split(" | Nyx responded:")[0].lstrip()
            if user_part.lower().startswith(("you:", "nyx:")):
                return False
            if user_part.startswith("/"):
                return False
            if any(user_part.startswith(cmd) for cmd in _SHELL_PREFIXES):
                return False
        return True

    before = len(memories)
    cleaned = [m for m in memories if is_clean(m)]
    removed = before - len(cleaned)

    deduped = dedup_memories(cleaned)
    dupes_removed = len(cleaned) - len(deduped)
    removed += dupes_removed

    if removed == 0:
        print("Nothing to remove — memory is already clean.")
        return

    save(MEMORY_PATH, deduped)
    print(f"Removed {removed} entr{'y' if removed == 1 else 'ies'} "
          f"({dupes_removed} duplicate{'s' if dupes_removed != 1 else ''}). "
          f"{len(deduped)} remaining.")


if __name__ == "__main__":
    main()
