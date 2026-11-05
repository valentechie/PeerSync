import json

import httpx
import pytest

from app.ai import llm_client
from app.ai.practice.coach import SYSTEM_PROMPT
from app.core.config import get_settings

NEXT = "/api/practice/next"
KEY = "clave-de-prueba"


@pytest.fixture
def gemini(monkeypatch):
    """Sustituye la llamada HTTP a Gemini y guarda las peticiones."""
    calls = []
    state = {"response": {"candidates": [{"content": {"parts": [{"text": "  ¿Por qué ocurre eso?  "}]}}]}, "status": 200}

    def fake_post(url, headers, json, timeout):
        calls.append({"url": url, "headers": headers, "json": json})
        request = httpx.Request("POST", url)
        return httpx.Response(state["status"], json=state["response"], request=request)

    monkeypatch.setattr(llm_client.httpx, "post", fake_post)
    monkeypatch.setattr(get_settings(), "gemini_api_key", KEY)
    return calls, state


def test_requires_a_token(client):
    assert client.post(NEXT, json={"topic": "x"}).status_code == 401


def test_first_question_sends_only_the_topic(client, auth_headers, gemini):
    calls, _ = gemini

    response = client.post(NEXT, json={"topic": "  Fotosíntesis  "}, headers=auth_headers())

    assert response.status_code == 200
    assert response.json() == {"question": "¿Por qué ocurre eso?"}
    call = calls[0]
    assert get_settings().gemini_model in call["url"]
    assert call["headers"]["x-goog-api-key"] == KEY
    assert call["json"]["systemInstruction"]["parts"][0]["text"] == SYSTEM_PROMPT
    assert [turn["role"] for turn in call["json"]["contents"]] == ["user"]
    assert "Fotosíntesis" in call["json"]["contents"][0]["parts"][0]["text"]


def test_conversation_is_sent_in_order_with_gemini_roles(client, auth_headers, gemini):
    calls, _ = gemini
    history = [{"role": "coach", "content": "Explícamelo"}, {"role": "student", "content": "Es un proceso"}]

    client.post(NEXT, json={"topic": "Fotosíntesis", "history": history}, headers=auth_headers())

    contents = calls[0]["json"]["contents"]
    assert [turn["role"] for turn in contents] == ["user", "model", "user"]
    assert [turn["parts"][0]["text"] for turn in contents[1:]] == ["Explícamelo", "Es un proceso"]


def test_no_personal_data_reaches_gemini(client, auth_headers, gemini):
    calls, _ = gemini

    client.post(NEXT, json={"topic": "Redes"}, headers=auth_headers(email="ana.garcia@hack4edu.org", name="Ana García"))

    sent = json.dumps(calls[0]["json"], ensure_ascii=False)
    assert "Ana García" not in sent
    assert "ana.garcia" not in sent


def test_prompt_forbids_answers_and_grades():
    assert "Never give the answer" in SYSTEM_PROMPT
    assert "Do not give grades" in SYSTEM_PROMPT


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"topic": "   "},
        {"topic": "x" * 121},
        {"topic": "x", "extra": 1},
        {"topic": "x", "history": [{"role": "student", "content": "a"}]},
        {"topic": "x", "history": [{"role": "coach", "content": "a"}]},
        {"topic": "x", "history": [{"role": "coach", "content": "a"}, {"role": "coach", "content": "b"}]},
        {"topic": "x", "history": [{"role": "coach", "content": "a"}, {"role": "student", "content": ""}]},
        {"topic": "x", "history": [{"role": "coach", "content": "a"}, {"role": "student", "content": "y" * 2001}]},
        {"topic": "x", "history": [{"role": "system", "content": "a"}, {"role": "student", "content": "b"}]},
        {"topic": "x", "history": [{"role": "coach", "content": "a"}, {"role": "student", "content": "b"}] * 21},
    ],
)
def test_invalid_input_is_rejected_without_calling_gemini(client, auth_headers, gemini, body):
    calls, _ = gemini

    assert client.post(NEXT, json=body, headers=auth_headers()).status_code == 422
    assert calls == []


def test_without_api_key_it_says_so_and_invents_nothing(client, auth_headers, monkeypatch):
    monkeypatch.setattr(get_settings(), "gemini_api_key", "")

    response = client.post(NEXT, json={"topic": "x"}, headers=auth_headers())

    assert response.status_code == 503
    assert response.json() == {"detail": "AI practice isn't configured yet"}


def test_gemini_error_returns_503_without_details(client, auth_headers, gemini):
    _, state = gemini
    state["status"] = 429
    state["response"] = {"error": {"message": f"detalle interno {KEY}"}}

    response = client.post(NEXT, json={"topic": "x"}, headers=auth_headers())

    assert response.status_code == 503
    assert KEY not in response.text
    assert "interno" not in response.text


def test_network_error_returns_503(client, auth_headers, gemini, monkeypatch):
    def fail(*_, **__):
        raise httpx.ConnectTimeout("sin conexión")

    monkeypatch.setattr(llm_client.httpx, "post", fail)

    assert client.post(NEXT, json={"topic": "x"}, headers=auth_headers()).status_code == 503


@pytest.mark.parametrize(
    "payload",
    [
        {"promptFeedback": {"blockReason": "SAFETY"}},
        {"candidates": []},
        {"candidates": [{"finishReason": "SAFETY"}]},
        {"candidates": [{"content": {"parts": [{"text": "   "}]}}]},
    ],
)
def test_blocked_or_empty_answer_returns_502(client, auth_headers, gemini, payload):
    _, state = gemini
    state["response"] = payload

    assert client.post(NEXT, json={"topic": "x"}, headers=auth_headers()).status_code == 502


def test_is_rate_limited(client, auth_headers, gemini):
    headers = auth_headers()

    statuses = [client.post(NEXT, json={"topic": "x"}, headers=headers).status_code for _ in range(31)]

    assert statuses == [200] * 30 + [429]
