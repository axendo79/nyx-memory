"""
Nyx file watcher — monitors Inbox for new files, summarizes via LLM,
stores the result in memory.
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from llm.client import query_llm
from memory.store import load_memories, save_memories, add_memory

load_dotenv()

INBOX_PATH = os.getenv("INBOX_PATH", r"D:\Nyx\Inbox")
MEMORY_PATH = os.path.join(os.path.dirname(__file__), "data", "memory.json")

# File extensions treated as readable text
TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".log", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".py", ".js", ".ts", ".html", ".xml",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [watcher] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def extract_text(filepath: str) -> str | None:
    """
    Read text from a file. Returns None if the file is binary or unreadable.
    Caps content at 4000 chars to keep LLM prompts reasonable.
    """
    _, ext = os.path.splitext(filepath)
    if ext.lower() not in TEXT_EXTENSIONS:
        log.info("Skipping non-text file: %s", os.path.basename(filepath))
        return None

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(4000)
        return content.strip() or None
    except OSError as e:
        log.warning("Could not read %s: %s", filepath, e)
        return None


def summarize_and_store(filepath: str) -> None:
    """Extract text, send to LLM for summarization, store in memory."""
    filename = os.path.basename(filepath)
    log.info("New file detected: %s", filename)

    text = extract_text(filepath)
    if not text:
        log.info("No readable content in %s — skipping.", filename)
        return

    prompt = (
        f"Summarize the following file content in 2-3 sentences. "
        f"Be concise. File: {filename}\n\n{text}"
    )

    log.info("Sending to LLM for summarization...")
    summary = query_llm(prompt)
    log.info("Summary: %s", summary)

    memories = load_memories(MEMORY_PATH)
    memories = add_memory(memories, f"[Inbox file: {filename}]", summary)
    save_memories(MEMORY_PATH, memories)
    log.info("Stored in memory.")


class InboxHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        # Brief delay to let the file finish writing before reading
        time.sleep(0.5)
        summarize_and_store(event.src_path)

    def on_moved(self, event):
        # Also catch files moved/copied into the inbox
        if event.is_directory:
            return
        time.sleep(0.5)
        summarize_and_store(event.dest_path)


def run():
    if not os.path.isdir(INBOX_PATH):
        log.error("INBOX_PATH does not exist: %s", INBOX_PATH)
        sys.exit(1)

    log.info("Watching inbox: %s", INBOX_PATH)
    log.info("Press Ctrl+C to stop.\n")

    handler = InboxHandler()
    observer = Observer()
    observer.schedule(handler, INBOX_PATH, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Stopping watcher.")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    run()
