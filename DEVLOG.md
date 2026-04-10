# Nyx Devlog

---

## 2026-04-10

### Session 1 — Polish layer: debug toggle + `/why`

- `DEBUG_MODE = False` by default. Toggle with `/debug on` / `/debug off` at the prompt.
- All ambient console noise (`[RETRIEVE]`, `[BOOST]`, `[DECAY]`, `[KNOWLEDGE]`) gated behind `DEBUG_MODE`. Quiet by default for daily use.
- `/why` command — shows a snapshot of the last retrieval: which memories were injected, which knowledge files matched, and scores at time of use. Snapshot is taken post-retrieval pre-boost, so scores reflect what the LLM actually saw.
- README irregularities fixed: `/selftest` corrected to `python selftest.py`, `nyx_logger.py` description updated (it's a shared logger used by 5 modules, not dead code), `__init__.py` files added to project tree.
- Commits: `5ce7b35`

### Session 2 — Polish layer: silence weak memory + soft reasoning labels

- `INJECT_THRESHOLD = 0.5` (env-configurable). Memories retrieved above `MIN_SCORE` but below `INJECT_THRESHOLD` are silently dropped from the prompt. The LLM sees nothing.
- Soft reasoning prefixes in the memory block, rule-based by source + score:
  - `source: dream` → `"Based on patterns I've noticed: "`
  - `source: user`, score ≥ 0.7 → `"You've mentioned: "`
  - `source: user`, score 0.5–0.69 → `"You once mentioned: "`
  - anything else → bare text
- Memory block now reads like reasoning, not a database dump.
- Commits: `def46c2`

### Session 3 — Memory behavior layer: source-weighted scoring, decay, boost

- Decay rates now vary by source: `user=0.05`, `dream=0.10`, `hypothesis=0.15`. Dream entries fade twice as fast, hypothesis three times.
- Boost on retrieval varies by source: `user=+0.5`, `dream=+0.25`, `hypothesis=0.0`. Hypothesis entries are never reinforced by retrieval — only confirmed explicitly.
- Retrieval ranking multiplied by source weight: `user=1.0`, `dream=0.6`, `hypothesis=0.3`. Affects which entries win when scores are close; stored score is untouched.
- `hypothesis` source type introduced as a first-class memory type alongside `user` and `dream`.
- 11/11 selftest passing throughout.
- Commits: `28e0d65`

### Session 4 — `/why` silenced vs injected fix

- `/why` previously labelled all retrieved memories as "injected" regardless of `INJECT_THRESHOLD`. Fixed.
- Snapshot now captures `source` per memory alongside `score` and `text`.
- `handle_why` splits on `INJECT_THRESHOLD` matching `build_prompt` logic exactly — injected and silenced displayed as separate sections.
- Commits: `3785c26`

### Session 5 — `session_log.py` and main.py wiring

- New file `session_log.py` — per-session structured decision log, separate from `nyx_logger.py`.
- Writes `logs/session_<timestamp>.json` on exit. Records retrieval, ingest, and dream events with timestamps.
- `finalize()` derives summary automatically: `memories_added`, `memories_rejected`, `near_misses`, `consolidations`.
- `log()` enforces `event` key — raises `ValueError` if missing. Schema is stable.
- Wired into `main.py` with `try/finally` — log writes on clean exit, Ctrl+C, and uncaught exceptions.
- `near_miss` field present in schema, always `False` until `store.py` surfaces dedup signals.
- Commits: `0943bd4`

### Session 6 — `demo.py` scripted comparison

- New file `demo.py` — scripted walkthrough, no user input required.
- Three modes: baseline (no memory), naive (store everything, no decay), Nyx (full system).
- Six hardcoded scenarios: two preferences, unrelated query, two recall turns, noise injection.
- Shows injection counts per mode per turn. `[filter]` noise suppressed via `redirect_stdout`.
- Demonstrates the gap: baseline can't recall, naive injects noise, Nyx recalls cleanly.
- Commits: `d0bdb96`

### Session 7 — Sanitizer hardening and README cleanup

- 7 Dream-specific patterns added to `_INJECTION_PATTERNS` in `store.py` (14 total).
- New patterns cover: format mimicry (`User said:`, `Nyx responded:`), self-directed rewrites, fabricated user statements, directive injection, header patterns.
- `system:` scoped to line-start only (`re.MULTILINE`) to avoid false positives on benign mid-sentence use.
- README updated: commands table expanded (`/debug on|off`, `/why`, `demo.py`), `session_log.py` and `demo.py` added to project structure, session log and sanitizer count added to Current Status and Security sections.
- Commits: `0f836c7`, `7d3b71f`

---
