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

---
