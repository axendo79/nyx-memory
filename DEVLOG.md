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

## 2026-04-10 (Session 2)

- /why command now correctly distinguishes injected vs silenced memories
- session_log.py added — per-session JSON log, event-derived summary, try/finally wiring
- demo.py added — scripted baseline vs naive vs Nyx comparison, 6 hardcoded scenarios
- Sanitizer hardened with 7 Dream-specific patterns (14 total), system: scoped to line-start
- README updated — demo instructions, session log mention, new commands, sanitizer count

## 2026-04-10 (Session 3) — Bug fixes from project analysis

Top 5 concerns identified via full codebase audit. Four fixed this session:

- `session_log.py` logs/ anchored to script location via `__file__`, not CWD — was silently writing logs to wrong directory when run from outside project root. Commit: `9d8c3e2`
- `add_memory` gains `max_response_len` param (default 200, backward compatible) — watcher now passes 500 for file summaries, preventing silent truncation of LLM-generated content. Commit: `9d8c3e2`
- `watcher.py` filelock added to `processed_files.json` — eliminates race condition when two inbox files arrive simultaneously. Lock held only during hash check and commit, not during LLM summarization. Commit: `c99b237`
- `selftest.py` test 9 now uses temp dir + mock patch instead of live Knowledge directory — passes on clean clone, no local state dependency. Commit: `a32a8f5`
- Deferred: `audit.py` O(n²) duplicate detection — not urgent at current memory scale.

## 2026-04-10 (Session 4) — Bug fixes from second project analysis

Top 5 concerns identified via full codebase audit (second pass). Three fixed, one deferred, one behavioral:

- `clean_memory.py` filelock added to `load()` and `save()` — uses same `.lock` file as `store.py`, prevents data corruption when run concurrently with `main.py` or `watcher.py`. Commit: `2ac55e8`
- Hardcoded Windows paths removed from `knowledge/retrieve.py` and `watcher.py` — `KNOWLEDGE_PATH` now resolves relative to script location via `__file__`. `INBOX_PATH` default removed entirely, startup guard handles `None` cleanly. Commit: `d5eb336`
- `SYSTEM_PROMPT` now configurable via env var in `llm/client.py` — default behavior unchanged, override in `.env` to tune persona without editing source. Commit: `31cc90c`
- Deferred: `knowledge/retrieve.py` reads all `.md` files on every query — needs caching strategy, defer until Knowledge directory is large enough to measure.
- Deferred: single-word knowledge queries silently return nothing (overlap threshold of 2) — behavioral, not a bug.

---
