import os
from dotenv import load_dotenv

load_dotenv()

MIN_SCORE = float(os.getenv("MIN_SCORE", 0.3))

_DECAY_BY_SOURCE = {
    "user":       0.05,
    "dream":      0.10,
    "hypothesis": 0.15,
}
_DECAY_DEFAULT = 0.05


def apply_decay(memories: list) -> list:
    for m in memories:
        rate = _DECAY_BY_SOURCE.get(m.get("source", ""), _DECAY_DEFAULT)
        m["score"] = round(m["score"] - rate, 4)
    return [m for m in memories if m["score"] >= MIN_SCORE]
