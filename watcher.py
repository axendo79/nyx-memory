"""
Nyx file watcher — monitors Inbox for new files, summarizes via LLM,
stores the result in memory.
"""

import hashlib
import json
import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from llm.client import query_llm
from memory.store import load_memories, save_memories, add_memory
from nyx_logger import get_logger

load_dotenv()

INBOX_PATH = os.getenv("INBOX_PATH", r"D:\Nyx\Inbox")
PROCESSED_HASHES_FILE = Path(os.getenv("NYX_DATA_DIR", "data")) / "processed_files.json"


def load_processed_hashes() -> set:
    if PROCESSED_HASHES_FILE.exists():
        with open(PROCESSED_HASHES_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_processed_hashes(hashes: set) -> None:
    with open(PROCESSED_HASHES_FILE, "w") as f:
        json.dump(list(hashes), f)


def file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()
MEMORY_PATH = os.getenv("MEMORY_PATH", os.path.join(os.path.dirname(__file__), "data", "memory.json"))

TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".log", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".py", ".js", ".ts", ".html", ".xml",
}

# Console logger for interactive feedback
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [watcher] %(message)s",
    datefmt="%H:%M:%S",
)
console = logging.getLogger("watcher.console")

# Structured file logger
log = get_logger("watcher")


def extract_text(filepath: str) -> str | None:
    """
    Read text from a file. Returns None if the file is binary or unreadable.
    Caps content at 4000 chars to keep LLM prompts reasonable.
    """
    _, ext = os.path.splitext(filepath)
    if ext.lower() not in TEXT_EXTENSIONS:
        console.info("Skipping non-text file: %s", os.path.basename(filepath))
        log.info("ingest event=skip_binary path=%s ext=%s", os.path.basename(filepath), ext)
        return None

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(4000)
        return content.strip() or None
    except OSError as e:
        console.warning("Could not read %s: %s", filepath, e)
        log.warning("ingest event=read_error path=%s error=%s", filepath, e)
        return None


def summarize_and_store(filepath: str) -> None:
    """Extract text, send to LLM for summarization, store in memory."""
    filename = os.path.basename(filepath)
    console.info("New file detected: %s", filename)
    log.info("ingest event=file_detected path=%s", filename)

    text = extract_text(filepath)
    if not text:
        console.info("No readable content in %s — skipping.", filename)
        log.info("ingest event=empty_content path=%s", filename)
        return

    prompt = (
        f"Summarize the following file content in 2-3 sentences. "
        f"Be concise. File: {filename}\n\n{text}"
    )

    console.info("Sending to LLM for summarization...")
    summary = query_llm(prompt)
    console.info("Summary: %s", summary)
    log.info("ingest event=summarized path=%s summary_len=%d", filename, len(summary))

    memories = load_memories(MEMORY_PATH)
    memories = add_memory(memories, f"[Inbox file: {filename}]", summary)
    save_memories(MEMORY_PATH, memories)
    console.info("Stored in memory.")
    log.info("ingest event=stored path=%s total_memories=%d", filename, len(memories))


class InboxHandler(FileSystemEventHandler):
    def __init__(self):
        self.processed = load_processed_hashes()

    def _handle(self, path: str) -> None:
        if not os.path.exists(path):
            return
        h = file_hash(path)
        if h in self.processed:
            return
        self.processed.add(h)
        save_processed_hashes(self.processed)
        summarize_and_store(path)

    def on_created(self, event):
        if event.is_directory:
            return
        time.sleep(0.5)
        self._handle(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        time.sleep(0.5)
        self._handle(event.dest_path)


def run():
    if not os.path.isdir(INBOX_PATH):
        console.error("INBOX_PATH does not exist: %s", INBOX_PATH)
        log.error("ingest event=startup_failed reason=inbox_missing path=%s", INBOX_PATH)
        sys.exit(1)

    console.info("Watching inbox: %s", INBOX_PATH)
    console.info("Press Ctrl+C to stop.\n")
    log.info("ingest event=startup inbox=%s", INBOX_PATH)

    handler = InboxHandler()
    observer = Observer()
    observer.schedule(handler, INBOX_PATH, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.info("Stopping watcher.")
        log.info("ingest event=shutdown")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    run()
