"""
Nyx - Local AI memory wrapper
Decay by default, reinforce what matters.
"""

import os
from dotenv import load_dotenv
from llm.client import query_llm
from memory.store import load_memories, save_memories, add_memory
from memory.retrieve import retrieve_relevant

load_dotenv()

MEMORY_PATH = os.getenv("MEMORY_PATH", os.path.join(os.path.dirname(__file__), "data", "memory.json"))
MIN_SCORE = float(os.getenv("MIN_SCORE", 0.3))


def build_prompt(user_input: str, memories: list) -> str:
    if memories:
        memory_block = "\n".join(f"- {m['text'][:100]}" for m in memories)
        return (
            f"Relevant context from memory:\n{memory_block}\n\n"
            f"User: {user_input}"
        )
    return f"User: {user_input}"


def handle_debug(query: str, memories: list) -> None:
    results = retrieve_relevant(query, memories, top_n=5, min_score=MIN_SCORE)
    if not results:
        print(f"\n[debug] No memories found for: {query!r}\n")
        return
    print(f"\n[debug] Top {len(results)} memories for: {query!r}")
    for i, m in enumerate(results, 1):
        print(f"  {i}. [score: {m['score']:.2f}] {m['text']}")
    print()


def run():
    print("Nyx is running. Type 'exit' to quit, '/debug <query>' to inspect memory.\n")
    memories = load_memories(MEMORY_PATH)

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

        # Retrieve top 3 relevant memories above score threshold
        relevant = retrieve_relevant(user_input, memories, top_n=3, min_score=MIN_SCORE)

        # Build prompt with injected memory context
        prompt = build_prompt(user_input, relevant)

        # Query local LLM
        response = query_llm(prompt)
        print(f"\nNyx: {response}\n")

        # Store this exchange as a new memory
        memories = add_memory(memories, user_input, response)
        save_memories(MEMORY_PATH, memories)


if __name__ == "__main__":
    run()
