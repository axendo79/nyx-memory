"""
Audit — read-only memory health check.
No LLM, no writes. Pure inspection.
Trigger: /audit
"""

import difflib
from typing import List, Dict


def run_audit(memories: List[Dict]) -> None:
    issues = 0

    print(f"\n[audit] Memory count: {len(memories)}")

    # Check 1: Missing required fields
    required = {"score", "source", "confidence", "text"}
    missing_field = []
    for i, m in enumerate(memories):
        missing = required - m.keys()
        if missing:
            missing_field.append((i, missing))

    if missing_field:
        print(f"[audit] WARN: {len(missing_field)} entr{'y' if len(missing_field) == 1 else 'ies'} missing fields:")
        for i, fields in missing_field:
            print(f"  [{i}] missing: {', '.join(fields)} | {memories[i].get('text', '')[:60]}")
        issues += len(missing_field)
    else:
        print("[audit] OK: All entries have required fields.")

    # Check 2: Very short entries
    short = [(i, m) for i, m in enumerate(memories) if len(m.get("text", "")) < 20]
    if short:
        print(f"[audit] WARN: {len(short)} short entr{'y' if len(short) == 1 else 'ies'} (under 20 chars):")
        for i, m in short:
            print(f"  [{i}] {m.get('text', '')!r}")
        issues += len(short)
    else:
        print("[audit] OK: No short entries.")

    # Check 3: Score sanity — dream entries scoring above top user entry
    user_scores = [m["score"] for m in memories if m.get("source") == "user"]
    dream_scores = [(i, m["score"]) for i, m in enumerate(memories) if m.get("source") == "dream"]
    top_user = max(user_scores) if user_scores else 0.0
    inflated = [(i, s) for i, s in dream_scores if s > top_user]
    if inflated:
        print(f"[audit] WARN: {len(inflated)} dream entr{'y' if len(inflated) == 1 else 'ies'} scoring above top user entry ({top_user:.2f}):")
        for i, s in inflated:
            print(f"  [{i}] score={s:.2f} | {memories[i].get('text', '')[:60]}")
        issues += len(inflated)
    else:
        print(f"[audit] OK: Dream scores within range (top user: {top_user:.2f}).")

    # Check 4: Duplicate clusters
    clusters = []
    seen = set()
    for i, m in enumerate(memories):
        if i in seen:
            continue
        cluster = [i]
        for j, n in enumerate(memories):
            if j <= i or j in seen:
                continue
            ratio = difflib.SequenceMatcher(None, m["text"], n["text"]).ratio()
            if ratio >= 0.85:
                cluster.append(j)
                seen.add(j)
        if len(cluster) > 1:
            clusters.append(cluster)
            seen.add(i)

    if clusters:
        print(f"[audit] WARN: {len(clusters)} duplicate cluster{'s' if len(clusters) != 1 else ''} found:")
        for cluster in clusters:
            print(f"  indices {cluster} — {memories[cluster[0]].get('text', '')[:60]}")
        issues += len(clusters)
    else:
        print("[audit] OK: No duplicate clusters.")

    # Summary
    print(f"\n[audit] {issues} issue{'s' if issues != 1 else ''} found.\n")
