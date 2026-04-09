import os
from dotenv import load_dotenv

load_dotenv()

DECAY_AMOUNT = 0.05
MIN_SCORE = float(os.getenv("MIN_SCORE", 0.3))


def apply_decay(memories: list) -> list:
    for m in memories:
        m["score"] = round(m["score"] - DECAY_AMOUNT, 4)
    return [m for m in memories if m["score"] >= MIN_SCORE]
