# ⚠️ ARCHIVED — Development continues at [nyx-core-v2](link when ready)

This repository represents Nyx v1 — the proof-of-concept build that 
validated the core architecture. It is preserved as a reference and 
historical record.

**Do not use this for new work.** The v2 rebuild addresses stability, 
atomicity, and integrity issues identified during v1 development.

Status: Parked as of April 30, 2026


# Nyx

Nyx is a local-first AI memory system for persistent context.

It selectively stores, scores, and recalls information over time — allowing a
local LLM to build continuity across conversations without storing everything.

---

## Current Status

- Stable memory storage with deduplication and decay
- Junk filtering and prompt injection sanitization on all write paths
- Retrieval with keyword + partial matching
- Dream synthesis working (manual trigger) — output sanitized before storage
- Knowledge layer — persistent `.md` files injected alongside memory context
- Dual ingest via watcher — summaries written to both memory and knowledge
- Cross-process file locking on all memory reads/writes
- Decay and retrieval thresholds unified via `MIN_SCORE` env — no zombie entries
- Boost only fires after confirmed LLM success — failed exchanges don't reinforce memory
- Console observability — `[RETRIEVE]`, `[BOOST]`, `[DECAY]`, `[KNOWLEDGE]` events gated behind `/debug on`
- Prompt discipline — system prompt tuned for concise, direct output
- Per-session structured JSON log written to `logs/session_<timestamp>.json` on exit
- 14-pattern sanitizer on all write paths including Dream output
- 11/11 selftest passing
- Built-in tools: `/debug`, `/debug on|off`, `/why`, `/audit`, `/dream`, `selftest.py`, `query_nyx.py --all`, `demo.py`

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
| `/debug on` | Enable verbose mode — show `[RETRIEVE]`, `[BOOST]`, `[DECAY]`, `[KNOWLEDGE]` |
| `/debug off` | Disable verbose mode (default) |
| `/debug <query>` | Show top matching memories for a query |
| `/debug all` | Dump all memories with scores |
| `/why` | Show what was injected and silenced on the last turn |
| `/dream` | Synthesize patterns from memory |
| `/audit` | Check memory health and stats |
| `python selftest.py` | Run built-in system validation |
| `python demo.py` | Scripted baseline vs naive vs Nyx comparison |
| `python query_nyx.py "query"` | Standalone memory query (respects MIN_SCORE) |
| `python query_nyx.py --all "query"` | Query including decayed memories |

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
├── session_log.py       # Per-session decision log (writes logs/session_<ts>.json)
├── demo.py              # Scripted baseline vs naive vs Nyx comparison
├── clean_memory.py      # One-time memory cleanup and dedup
├── selftest.py          # Built-in system validation (run directly)
├── watcher.py           # Inbox file watcher
├── nyx_logger.py        # Shared structured logger (used by all modules)
├── query_nyx.py         # Standalone memory query tool
├── llm/
│   ├── __init__.py
│   └── client.py        # LLM endpoint client
├── memory/
│   ├── __init__.py
│   ├── store.py         # Save/load/score/dedup memories
│   ├── retrieve.py      # Keyword retrieval with scoring
│   ├── decay.py         # Score decay and pruning
│   ├── dream.py         # Dream Cycle synthesis
│   └── audit.py         # Memory health checks
├── knowledge/
│   ├── __init__.py
│   └── retrieve.py      # Keyword retrieval over Knowledge/*.md files
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
- `logs/` is gitignored — session logs stay local
- LM Studio endpoint is localhost only — never expose externally
- 14-pattern sanitizer strips prompt injection and Dream format mimicry from all write paths

---

## Roadmap

> Last updated: 2026-04-10 — actively developed

- **Improved retrieval** — content-aware matching beyond keyword overlap
- **Tunable decay** — per-entry decay controls via `.env`
- **Personality emergence** — let reinforced patterns shape response style
- **Knowledge management** — commands to list, remove, or inspect knowledge files

---

## Support

If Nyx is useful to you, a small tip is appreciated:
[Venmo @Joshua-Holliday-15](https://venmo.com/Joshua-Holliday-15)
