"""Peticiones simultáneas de verdad. Solo con PostgreSQL: SQLite no bloquea filas.

TEST_DATABASE_URL=<postgres desechable> pytest tests/test_contrasta_flow_concurrency.py
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from app.ai import deepseek_client
from app.core.config import get_settings
from conftest import TEST_DATABASE_URL, join_room

pytestmark = pytest.mark.skipif(TEST_DATABASE_URL.startswith("sqlite"), reason="Necesita PostgreSQL")

ROOMS = "/api/rooms"
COMPARISON = {"agreements": [], "differences": [], "questions": ["Why?"], "claims_to_verify": [], "uncertainty_note": "May be wrong."}


@pytest.fixture
def pair(client, auth_headers):
    ana = auth_headers(email="ana.conc@hack4edu.org", name="Ana")
    luis = auth_headers(email="luis.conc@hack4edu.org", name="Luis")
    room_id = client.post(ROOMS, json={"title": "Punteros", "objective": ""}, headers=ana).json()["id"]
    assert join_room(client, room_id, luis).status_code == 200
    partner = client.get("/api/profiles/me", headers=luis).json()["id"]
    response = client.post(f"{ROOMS}/{room_id}/contrasta/rounds", json={"prompt": "p++", "partnerId": partner}, headers=ana)
    assert response.status_code == 201
    return room_id, ana, luis


def _both(*requests):
    with ThreadPoolExecutor(max_workers=len(requests)) as pool:
        return [future.result() for future in [pool.submit(request) for request in requests]]


def _reveal(client, room_id, ana, luis):
    url = f"{ROOMS}/{room_id}/contrasta/answers"
    for headers, answer in ((ana, "a"), (luis, "b")):
        assert client.post(url, json={"answer": answer}, headers=headers).status_code == 201


def test_two_last_answers_reveal_once_with_both(client, pair):
    room_id, ana, luis = pair
    url = f"{ROOMS}/{room_id}/contrasta/answers"
    responses = _both(
        lambda: client.post(url, json={"answer": "a"}, headers=ana),
        lambda: client.post(url, json={"answer": "b"}, headers=luis),
    )
    assert [response.status_code for response in responses] == [201, 201]
    for headers in (ana, luis):
        round_ = client.get(f"{ROOMS}/{room_id}/contrasta/flow", headers=headers).json()["round"]
        assert round_["status"] == "revealed"
        assert {answer["answer"] for answer in round_["answers"]} == {"a", "b"}


def test_simultaneous_comparison_calls_the_ai_once_and_chat_keeps_working(client, pair, monkeypatch):
    room_id, ana, luis = pair
    _reveal(client, room_id, ana, luis)
    calls = []

    def slow_post(url, headers, json, timeout):
        calls.append(json)
        time.sleep(1.5)
        return httpx.Response(200, json=_completion(), request=httpx.Request("POST", url))

    monkeypatch.setattr(deepseek_client.httpx, "post", slow_post)
    monkeypatch.setattr(get_settings(), "deepseek_api_key", "clave-de-prueba")
    started = time.monotonic()
    url = f"{ROOMS}/{room_id}/contrasta/comparison"
    results = _both(
        lambda: client.post(url, headers=ana),
        lambda: client.post(url, headers=luis),
        # La sala no queda bloqueada mientras responde la IA.
        lambda: (time.sleep(0.3), client.post(f"{ROOMS}/{room_id}/messages", json={"content": "Sigo"}, headers=luis), time.monotonic() - started)[1:],
    )
    message, elapsed = results[2]
    assert results[0].status_code == 200 and results[1].status_code == 200
    assert message.status_code == 201 and elapsed < 1.4
    assert len(calls) == 1
    assert client.get(f"{ROOMS}/{room_id}/contrasta/flow", headers=ana).json()["comparison"]["status"] == "ready"


def _completion():
    return {"choices": [{"message": {"content": json.dumps(COMPARISON)}}]}


def test_simultaneous_proposals_create_one_activity(client, pair):
    room_id, ana, luis = pair
    _reveal(client, room_id, ana, luis)
    url = f"{ROOMS}/{room_id}/contrasta/activities"
    responses = _both(
        lambda: client.post(url, json={"concept": "A"}, headers=ana),
        lambda: client.post(url, json={"concept": "B"}, headers=luis),
    )
    assert [response.status_code for response in responses] == [200, 200]
    assert len(client.get(f"{ROOMS}/{room_id}/contrasta/flow", headers=ana).json()["activities"]) == 1


def test_simultaneous_accepts_keep_one_active_activity(client, pair):
    room_id, ana, luis = pair
    _reveal(client, room_id, ana, luis)
    client.post(f"{ROOMS}/{room_id}/contrasta/activities", json={"concept": "A"}, headers=ana)
    activity_id = client.get(f"{ROOMS}/{room_id}/contrasta/flow", headers=luis).json()["activities"][0]["id"]
    url = f"{ROOMS}/{room_id}/contrasta/activities/{activity_id}/respond/accept"
    responses = _both(lambda: client.post(url, headers=luis), lambda: client.post(url, headers=luis))
    assert [response.status_code for response in responses] == [200, 200]
    flow = client.get(f"{ROOMS}/{room_id}/contrasta/flow", headers=ana).json()
    assert [activity["status"] for activity in flow["activities"]] == ["active"]


def test_simultaneous_round_starts_create_one_round(client, auth_headers):
    ana = auth_headers(email="ana.ini@hack4edu.org", name="Ana")
    luis = auth_headers(email="luis.ini@hack4edu.org", name="Luis")
    room_id = client.post(ROOMS, json={"title": "R", "objective": ""}, headers=ana).json()["id"]
    assert join_room(client, room_id, luis).status_code == 200
    ana_id = client.get("/api/profiles/me", headers=ana).json()["id"]
    luis_id = client.get("/api/profiles/me", headers=luis).json()["id"]
    url = f"{ROOMS}/{room_id}/contrasta/rounds"
    responses = _both(
        lambda: client.post(url, json={"prompt": "A", "partnerId": luis_id}, headers=ana),
        lambda: client.post(url, json={"prompt": "B", "partnerId": ana_id}, headers=luis),
    )
    assert sorted(response.status_code for response in responses) == [201, 409]
