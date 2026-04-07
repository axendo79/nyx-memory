"""
LLM client — talks to LM Studio via OpenAI-compatible endpoint.
Swap base_url to point at any compatible local server.
"""

import os
import time
import requests

from nyx_logger import get_logger

log = get_logger("llm")

LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1/chat/completions")
MODEL_NAME = os.getenv("MODEL_NAME", "local-model")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 512))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))


def query_llm(prompt: str) -> str:
    """
    Send prompt to local LLM, return response text.
    Returns error string on failure rather than crashing.
    """
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are Nyx. Be concise and direct."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }

    log.info("llm event=request prompt_len=%d model=%s max_tokens=%d", len(prompt), MODEL_NAME, MAX_TOKENS)
    t0 = time.monotonic()

    try:
        response = requests.post(
            LM_STUDIO_URL,
            json=payload,
            timeout=120,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            log.warning("llm event=empty_response elapsed=%.2fs", time.monotonic() - t0)
            return "[No response from model]"

        text = choices[0]["message"]["content"].strip()
        log.info("llm event=response response_len=%d elapsed=%.2fs", len(text), time.monotonic() - t0)
        return text

    except requests.exceptions.ConnectionError:
        log.error("llm event=connection_error url=%s", LM_STUDIO_URL)
        return "[Error: Cannot connect to LM Studio. Is it running on port 1234?]"
    except requests.exceptions.Timeout:
        log.error("llm event=timeout elapsed=%.2fs", time.monotonic() - t0)
        return "[Error: LM Studio timed out]"
    except Exception as e:
        log.error("llm event=error error=%s", e)
        return f"[Error: {e}]"
