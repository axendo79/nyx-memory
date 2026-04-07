"""
LLM client — talks to LM Studio via OpenAI-compatible endpoint.
Swap base_url to point at any compatible local server.
"""

import os
import requests

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

    try:
        response = requests.post(
            LM_STUDIO_URL,
            json=payload,
            timeout=120,
            # No external calls — localhost only
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return "[No response from model]"
        return choices[0]["message"]["content"].strip()

    except requests.exceptions.ConnectionError:
        return "[Error: Cannot connect to LM Studio. Is it running on port 1234?]"
    except requests.exceptions.Timeout:
        return "[Error: LM Studio timed out]"
    except Exception as e:
        return f"[Error: {e}]"
