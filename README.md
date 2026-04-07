# Nyx

> Decay by default, reinforce what matters.

Nyx is a local-first AI memory wrapper. Instead of storing everything, memory persists only through repeated relevance — forming a more human-like conversational identity over time.

## What it does

- Wraps any OpenAI-compatible local LLM (LM Studio, KoboldCPP, etc.)
- Stores conversation memories in a local JSON file
- Retrieves relevant memories and injects them into each prompt
- Scores memories on retrieval — unused memories decay and are pruned

## Quickstart

```bash
# 1. Clone and enter the repo
git clone https://github.com/yourname/nyx-memory
cd nyx-memory

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env to match your LM Studio model name

# 5. Run
python main.py
```

## Requirements

- Python 3.10+
- LM Studio running on localhost:1234 (or any OpenAI-compatible endpoint)

## Project structure

```
nyx/
├── main.py              # Main loop
├── llm/
│   └── client.py        # LLM endpoint client
├── memory/
│   ├── store.py         # Save/load/score memories
│   └── retrieve.py      # Keyword retrieval
├── data/
│   └── memory.json      # Local memory storage (gitignored)
├── .env.example         # Config template
├── .gitignore
└── requirements.txt
```

## Memory system

Each memory entry:
```json
{
  "text": "User said: ... | Nyx responded: ...",
  "score": 1.0,
  "last_used": 1234567890,
  "created": 1234567890
}
```

- Score increases on retrieval
- Score decays over time via `apply_decay()`
- Entries below `MIN_SCORE` threshold are pruned

## Security

- `.env` is gitignored — never commit secrets
- `data/memory.json` is gitignored — memory stays local
- LM Studio endpoint is localhost only — never expose externally

## Roadmap

- **Robust retrieval** — replace keyword overlap with embedding-based semantic search so memories surface by meaning, not just shared words
- **Tunable decay rates** — per-entry and global decay controls, configurable via `.env`, allowing fine-grained control over how quickly memories fade
- **Voice / avatar hooks** — plugin points for TTS output and a visual avatar layer, so Nyx can speak responses and present a face tied to its memory state
- **Personality emergence** — track which topics and tones are most reinforced over time, and let those patterns shape Nyx's default voice and response style organically
