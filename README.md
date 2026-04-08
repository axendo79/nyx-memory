# Nyx

Nyx is a local-first AI memory system for persistent context.

It selectively stores, scores, and recalls information over time — allowing a
local LLM to build continuity across conversations without storing everything.

---

## Current Status

- Stable memory storage with deduplication and decay
- Junk filtering on ingest
- Retrieval with keyword + partial matching
- Dream synthesis working (manual trigger)
- Built-in tools: `/debug`, `/audit`, `/selftest`

Actively being developed and tested with real usage.

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

## Example

```
You: "I prefer working in short focused sessions."

Later:

You: "How do I work best?"
Nyx: "You prefer working in short focused sessions."
```

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

## Commands

| Command | Description |
|---|---|
| `/debug <query>` | Show top matching memories for a query |
| `/debug all` | Dump all memories with scores |
| `/dream` | Synthesize patterns from memory |
| `/audit` | Check memory health and stats |
| `/selftest` | Run built-in system validation |

---

## Dream Cycle

Nyx can synthesize patterns from memory using `/dream`.

It selects high-confidence memories, sends them to the LLM for reflection,
and stores the result as a low-confidence inferred memory. This allows
interests and patterns to emerge over time without overwriting original data.

Dream entries are marked `source: dream, confidence: low` and never feed
back into future synthesis cycles.

---

## Project structure

```
nyx/
├── main.py              # Main loop and command handling
├── clean_memory.py      # One-time memory cleanup and dedup
├── selftest.py          # Built-in system validation
├── watcher.py           # Inbox file watcher
├── nyx_logger.py        # Logging
├── query_nyx.py         # Standalone memory query tool
├── llm/
│   └── client.py        # LLM endpoint client
├── memory/
│   ├── store.py         # Save/load/score/dedup memories
│   ├── retrieve.py      # Keyword retrieval with scoring
│   ├── dream.py         # Dream Cycle synthesis
│   └── audit.py         # Memory health checks
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
  "uses": 2,
  "source": "user",
  "confidence": "medium",
  "created": 1234567890,
  "last_used": 1234567890
}
```

- Score increases on retrieval
- Score decays over time via `apply_decay()`
- Entries below `MIN_SCORE` threshold are pruned
- Near-duplicate entries (≥85% similarity) are collapsed on ingest
- Dream entries start at score 0.8 and decay faster than user memories

---

## Security

- `.env` is gitignored — never commit secrets
- `data/memory.json` is gitignored — memory stays local
- LM Studio endpoint is localhost only — never expose externally

---

## Roadmap

- **Improved retrieval** — content-aware matching beyond keyword overlap
- **Faster dream decay** — dream entries should fade unless reinforced
- **Tunable decay** — per-entry decay controls via `.env`
- **Personality emergence** — let reinforced patterns shape response style

---

## Support

If Nyx is useful to you, a small tip is appreciated:
[Venmo @Joshua-Holliday-15](https://venmo.com/Joshua-Holliday-15)
