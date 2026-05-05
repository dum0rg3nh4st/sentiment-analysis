import os
from typing import Any, Dict, List, Tuple

import httpx


MODEL_ID = "distilbert-base-uncased-finetuned-sst-2-english"
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{MODEL_ID}"


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Set it in your .env (see .env.example)."
        )
    return value


def _map_label(raw_label: str) -> str:
    # Model card mapping for distilbert-base-uncased-finetuned-sst-2-english:
    # NEGATIVE -> NEGATIVE, POSITIVE -> POSITIVE
    # Also handles numeric LABEL_x format as a fallback:
    # LABEL_0 -> NEGATIVE, LABEL_1 -> POSITIVE
    s = (raw_label or "").strip().upper()
    if s in {"NEUTRAL", "POSITIVE", "NEGATIVE"}:
        return s
    # Fallback: numeric LABEL_x format
    if "0" in s:
        return "NEGATIVE"
    if "1" in s:
        return "POSITIVE"
    if "2" in s:
        return "NEGATIVE"
    return "NEUTRAL"


def _extract_items(data: Any) -> List[Dict[str, Any]]:
    # Expected shapes:
    # - [ {label, score}, ... ]
    # - [ [ {label, score}, ... ] ]
    if isinstance(data, list) and data and isinstance(data[0], list):
        data = data[0]
    if not isinstance(data, list):
        raise ValueError("Unexpected HF response shape.")
    return [x for x in data if isinstance(x, dict)]


async def predict_sentiment(text: str) -> Tuple[str, float]:
    """
    Calls Hugging Face Inference API.

    Security note:
    - HF_TOKEN is read from environment at runtime (server-side) and never returned to clients.
    """
    token = _require_env("HF_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": text, "options": {"wait_for_model": True}}

    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(HF_API_URL, headers=headers, json=payload)

    # HF returns useful errors as JSON like: { "error": "...", "estimated_time": ... }
    if resp.status_code >= 400:
        try:
            j = resp.json()
            message = j.get("error") or str(j)
        except Exception:
            message = resp.text or f"HTTP {resp.status_code}"
        raise RuntimeError(f"Hugging Face API error: {message}")

    data = resp.json()
    items = _extract_items(data)
    if not items:
        raise RuntimeError("Empty response from Hugging Face.")

    best = max(items, key=lambda x: float(x.get("score", 0.0)))
    label = _map_label(str(best.get("label", "")))
    score = float(best.get("score", 0.0))
    return label, score

