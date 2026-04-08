# Nyx

Nyx is a local-first AI memory system for persistent context.

It selectively stores, scores, and recalls information over time — allowing a
local LLM to build continuity across conversations without storing everything.

---

## What it does

- Adds persistent memory to any OpenAI-compatible local LLM (LM Studio, KoboldCPP, etc.)
- Stores conversation memories in a local JSON file
- Retrieves relevant memories and injects them into each prompt
- Scores memories on retrieval — unused memories decay and are pruned
- Deduplicates on ingest — similar memories update score instead of creating duplicates
- Debug visibility via `/debug <query>` and `/debug all`

## What this is NOT

- Not a pentesting tool or MCP server
- Not a vector database or RAG framework
- Not a full agent system

Nyx focuses specifically on long-term memory: what to keep, what to forget,
and what to surface.

---

## Quickstart

```bash
# 1. Clone and enter the repo
git clone https://github.com/axendo79/nyx-memory
cd nyx-memory

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env to match your LM Studio model name

# 5. Run
python main.py
```

---

## Requirements

- Python 3.10+
- LM Studio running on localhost:1234 (or any OpenAI-compatible endpoint)

---

## Project structure

```
nyx/
├── main.py              # Main loop and debug commands
├── clean_memory.py      # One-time memory cleanup and dedup
├── watcher.py           # Inbox file watcher
├── nyx_logger.py        # Logging
├── query_nyx.py         # Standalone memory query tool
├── llm/
│   └── client.py        # LLM endpoint client
├── memory/
│   ├── store.py         # Save/load/score/dedup memories
│   └── retrieve.py      # Keyword retrieval with scoring
├── data/
│   └── memory.json      # Local memory storage (gitignored)
├── .env.example         # Config template
├── .gitignore
└── requirements.txt
```

---

## Memory system

Each memory entry:

```json
{
  "text": "User said: ... | Nyx responded: ...",
  "score": 1.0,
  "last_used": 1234567890,
  "created": 1234567890,
  "source": "conversation",
  "confidence": 1.0,
  "uses": 0
}
```

**Fields:**

| Field | Description |
|---|---|
| `text` | Raw memory content |
| `score` | Retrieval weight — increases on use, decays over time |
| `last_used` | Unix timestamp of last retrieval |
| `created` | Unix timestamp of creation |
| `source` | Origin: `conversation`, `watcher`, or `dream` |
| `confidence` | Ingest confidence (0.0–1.0) |
| `uses` | Number of times retrieved |

- Score increases on retrieval
- Score decays over time via `apply_decay()`
- Entries below `MIN_SCORE` threshold are pruned
- Near-duplicate entries (≥85% similarity) are collapsed on ingest,
  boosting the existing entry instead of writing a new one

---

## Debug commands

| Command | Description |
|---|---|
| `/debug <query>` | Show top matching memories for a query |
| `/debug all` | Dump all memories with scores (diagnostic) |

---

## Security

- `.env` is gitignored — never commit secrets
- `data/memory.json` is gitignored — memory stays local
- LM Studio endpoint is localhost only — never expose externally

---

## Commands

| Command | Description |
|---|---|
| `/debug <query>` | Show top matching memories for a query |
| `/debug all` | Dump all memories with scores |
| `/dream` | Synthesize new memories from top-scored existing ones |
| `/audit` | Show memory stats: count, avg score, sources, confidence |

---

## Roadmap

- **Tunable decay** — per-entry and global decay controls,
  configurable via `.env`
- **Personality emergence** — track which topics and tones are most
  reinforced over time and let those patterns shape Nyx's default
  response style organically
