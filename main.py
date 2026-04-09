"""
Nyx - Local AI memory wrapper
Decay by default, reinforce what matters.
"""

import os
from dotenv import load_dotenv
from llm.client import query_llm
from memory.store import load_memories, save_memories, add_memory, boost_score
from memory.retrieve import retrieve_relevant
from memory.dream import run_dream
from memory.audit import run_audit
from memory.decay import apply_decay
from knowledge.retrieve import retrieve_knowledge

load_dotenv()

MEMORY_PATH = os.getenv("MEMORY_PATH", os.path.join(os.path.dirname(__file__), "data", "memory.json"))
MIN_SCORE = float(os.getenv("MIN_SCORE", 0.3))


def build_prompt(user_input: str, memories: list, knowledge: list = None) -> str:
    parts = []
    if knowledge:
        context = "\n\n".join(
            f"[{k['name']}]\n{k['content'][:500]}"
            for k in knowledge
        )
        parts.append(f"Relevant knowledge:\n{context}")
    if memories:
        memory_block = "\n".join(f"- {m['text'][:100]}" for m in memories)
        parts.append(f"Relevant memory:\n{memory_block}")
    parts.append(f"User: {user_input}")
    return "\n\n".join(parts)


def handle_debug(query: str, memories: list) -> None:
    if query == "all":
        print(f"\n[debug] All memories ({len(memories)} total):")
        for m in memories:
            print(f"  score={m['score']:.2f} | {m['text'][:80]}")
        print()
        return

    results = retrieve_relevant(query, memories, top_n=5, min_score=MIN_SCORE)
    if not results:
        print(f"\n[debug] No memories found for: {query!r}\n")
        return
    print(f"\n[debug] Top {len(results)} memories for: {query!r}")
    for i, m in enumerate(results, 1):
        print(f"  {i}. [score: {m['score']:.2f}] {m['text']}")
    print()


def run():
    print("Nyx is running. Type 'exit' to quit, '/debug <query>' to inspect memory, '/dream' to synthesize.\n")
    memories = load_memories(MEMORY_PATH)

    original_count = len(memories)
    memories = apply_decay(memories)
    if len(memories) != original_count:
        save_memories(MEMORY_PATH, memories)
        print(f"[DECAY] pruned={original_count - len(memories)} remaining={len(memories)}")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("Nyx stopped.")
            break

        if user_input.startswith("/debug "):
            handle_debug(user_input[7:].strip(), memories)
            continue

        if user_input == "/dream":
            memories = run_dream(memories, MEMORY_PATH)
            continue

        if user_input == "/audit":
            run_audit(memories)
            continue

        # Retrieve top 3 relevant memories above score threshold
        relevant = retrieve_relevant(user_input, memories, top_n=3, min_score=MIN_SCORE)
        print(f"[RETRIEVE] found={len(relevant)} top_score={relevant[0]['score']:.2f}" if relevant else "[RETRIEVE] found=0")

        # Build prompt with injected memory context
        knowledge = retrieve_knowledge(user_input)
        print(f"[KNOWLEDGE] found={len(knowledge)}")
        prompt = build_prompt(user_input, relevant, knowledge)

        # Query local LLM
        response = query_llm(prompt)
        print(f"\nNyx: {response}\n")

        if not response.startswith("[Error"):
            for m in relevant:
                boost_score(m)
                print(f"[BOOST] score boosted to {m['score']:.2f}")

        # Store this exchange as a new memory
        memories = add_memory(memories, user_input, response)
        original_count_loop = len(memories)
        memories = apply_decay(memories)
        if len(memories) != original_count_loop:
            print(f"[DECAY] pruned={original_count_loop - len(memories)} remaining={len(memories)}")
        save_memories(MEMORY_PATH, memories)


if __name__ == "__main__":
    run()
