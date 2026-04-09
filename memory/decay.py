DECAY_AMOUNT = 0.05
MIN_SCORE = 0.1


def apply_decay(memories: list) -> list:
    for m in memories:
        m["score"] = round(m["score"] - DECAY_AMOUNT, 4)
    return [m for m in memories if m["score"] >= MIN_SCORE]
