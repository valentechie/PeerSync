"""Único punto de contacto con Gemini. No registra nunca prompts ni la API key."""

from collections.abc import Sequence
from typing import Literal

import httpx

from app.core.config import get_settings

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TIMEOUT_SECONDS = 25
MAX_OUTPUT_TOKENS = 800

Role = Literal["user", "model"]


class LLMNotConfiguredError(Exception):
    pass


class LLMUnavailableError(Exception):
    pass


class LLMEmptyResponseError(Exception):
    """Gemini bloqueó el contenido o no devolvió texto."""


def generate(system: str, turns: Sequence[tuple[Role, str]]) -> str:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise LLMNotConfiguredError
    try:
        response = httpx.post(
            GEMINI_URL.format(model=settings.gemini_model),
            headers={"x-goog-api-key": settings.gemini_api_key},
            json={
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": role, "parts": [{"text": text}]} for role, text in turns],
                "generationConfig": {"maxOutputTokens": MAX_OUTPUT_TOKENS},
            },
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise LLMUnavailableError from exc

    candidates = data.get("candidates") or []
    parts = (candidates[0].get("content") or {}).get("parts") or [] if candidates else []
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise LLMEmptyResponseError
    return text
