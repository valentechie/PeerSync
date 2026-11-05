import json
from uuid import uuid4

import httpx
import pytest

from app.ai import deepseek_client
from app.ai.studymind.hint_generator import LADDER
from app.core.config import get_settings
from conftest import join_room

ROOMS = "/api/rooms"
KEY = "clave-de-prueba"
HELP = {"message": "¿Qué parte se te resiste?", "suggested_action": "Resúmesela a tu compañero.", "uncertainty_note": "Puede faltar contexto."}
FEEDBACK = {
    "strengths": ["Se ha explicado la idea principal."],
    "possible_gaps": ["Falta justificar el caso límite."],
    "questions_for_peer": ["¿Qué ocurre si el tamaño es cero?"],
    "evidence_to_check": ["El requisito exacto del ejercicio."],
    "suggested_peer_activity": "Intercambiad los roles y proponed un ejemplo nuevo.",
    "uncertainty_note": "Conviene contrastarlo con la fuente.",
}


def completion(output):
    content = output if isinstance(output, str) else json.dumps(output)
    return {"choices": [{"message": {"content": content}}]}


@pytest.fixture
def deepseek(monkeypatch):
    calls = []
    state = {"response": completion(HELP), "status": 200}

    def fake_post(url, headers, json, timeout):
        calls.append(json)
        return httpx.Response(state["status"], json=state["response"], request=httpx.Request("POST", url))

    monkeypatch.setattr(deepseek_client.httpx, "post", fake_post)
    monkeypatch.setattr(get_settings(), "deepseek_api_key", KEY)
    return calls, state


@pytest.fixture
def ana(auth_headers):
    return auth_headers(email="ana.privada@hack4edu.org", name="Ana Privada")


@pytest.fixture
def bea(auth_headers):
    return auth_headers(email="bea.privada@hack4edu.org", name="Bea Privada")


@pytest.fixture
def room_id(client, ana, bea):
    id_ = client.post(ROOMS, json={"title": "Libft", "objective": "Entender ft_calloc"}, headers=ana).json()["id"]
    assert join_room(client, id_, bea).status_code == 200
    return id_


def _help(client, room_id, headers, **body):
    return client.post(f"{ROOMS}/{room_id}/ai/studymind", json={"difficulty": "No entiendo el tamaño cero", **body}, headers=headers)


def _explain(client, room_id, headers):
    response = client.post(
        f"{ROOMS}/{room_id}/teachback",
        json={"concept": "ft_calloc", "explanation": "Reserva memoria y la pone a cero"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _review(client, room_id, submission_id, headers):
    return client.post(f"{ROOMS}/{room_id}/teachback/{submission_id}/review", json={"comment": "He entendido la reserva"}, headers=headers)


# StudyMind

def test_studymind_requires_token_membership_and_a_request(client, auth_headers, room_id, ana):
    assert client.post(f"{ROOMS}/{room_id}/ai/studymind", json={"difficulty": "x"}).status_code == 401
    outsider = auth_headers(email="fuera@hack4edu.org", name="Fuera")
    assert _help(client, room_id, outsider).status_code == 403
    assert client.post(f"{ROOMS}/{room_id}/ai/studymind", json={}, headers=ana).status_code == 422
    assert _help(client, uuid4(), ana).status_code == 404


@pytest.mark.parametrize("step", [0, 7])
def test_studymind_rejects_steps_outside_the_ladder(client, room_id, ana, step):
    assert _help(client, room_id, ana, step=step).status_code == 422


def test_studymind_starts_at_the_first_step(client, room_id, ana, deepseek):
    calls, _ = deepseek

    response = _help(client, room_id, ana)

    assert response.status_code == 200
    assert response.json() == {"source": "ai", "step": 1, "message": HELP["message"], "suggestedAction": HELP["suggested_action"], "uncertaintyNote": HELP["uncertainty_note"]}
    assert "peer" in LADDER[1]
    assert LADDER[1] in calls[-1]["messages"][1]["content"]


@pytest.mark.parametrize("step", sorted(LADDER))
def test_studymind_sends_the_goal_of_the_requested_step(client, room_id, ana, deepseek, step):
    calls, _ = deepseek

    assert _help(client, room_id, ana, step=step).json()["step"] == step
    assert LADDER[step] in calls[-1]["messages"][1]["content"]


def test_studymind_sends_only_topic_and_difficulty(client, room_id, ana, deepseek):
    calls, _ = deepseek
    client.post(f"{ROOMS}/{room_id}/messages", json={"content": "Mensaje del chat"}, headers=ana)

    _help(client, room_id, ana)

    sent = json.dumps(calls[-1], ensure_ascii=False)
    for private in ("Ana Privada", "ana.privada@hack4edu.org", "Mensaje del chat", KEY):
        assert private not in sent


@pytest.mark.parametrize("step", sorted(LADDER))
def test_studymind_falls_back_without_ai(client, room_id, ana, step):
    response = _help(client, room_id, ana, step=step)

    assert response.status_code == 200
    assert response.json()["source"] == "fallback"
    assert response.json()["step"] == step


def test_studymind_falls_back_on_invalid_output(client, room_id, ana, deepseek):
    _, state = deepseek
    state["response"] = completion("no es JSON")

    assert _help(client, room_id, ana).json()["source"] == "fallback"


# TeachBack

def test_teachback_requires_token_and_membership(client, auth_headers, room_id, ana):
    submission_id = _explain(client, room_id, ana)
    assert client.get(f"{ROOMS}/{room_id}/teachback").status_code == 401
    outsider = auth_headers(email="fuera@hack4edu.org", name="Fuera")
    assert client.get(f"{ROOMS}/{room_id}/teachback", headers=outsider).status_code == 403
    assert client.post(f"{ROOMS}/{room_id}/teachback", json={"concept": "x", "explanation": "y"}, headers=outsider).status_code == 403
    assert _review(client, room_id, submission_id, outsider).status_code == 403
    assert client.post(f"{ROOMS}/{room_id}/teachback/{submission_id}/ai-feedback", headers=outsider).status_code == 403


def test_ai_feedback_is_refused_before_the_peer_review(client, room_id, ana, deepseek):
    calls, _ = deepseek
    submission_id = _explain(client, room_id, ana)

    response = client.post(f"{ROOMS}/{room_id}/teachback/{submission_id}/ai-feedback", headers=ana)

    assert response.status_code == 409
    assert calls == []


def test_explainer_cannot_review_themselves(client, room_id, ana):
    submission_id = _explain(client, room_id, ana)

    assert _review(client, room_id, submission_id, ana).status_code == 403


def test_explanation_has_a_single_review(client, auth_headers, room_id, ana, bea):
    submission_id = _explain(client, room_id, ana)
    assert _review(client, room_id, submission_id, bea).status_code == 201
    cris = auth_headers(email="cris@hack4edu.org", name="Cris")
    join_room(client, room_id, cris)

    assert _review(client, room_id, submission_id, cris).status_code == 409


def test_submission_of_another_room_is_not_reachable(client, room_id, ana, bea):
    other = client.post(ROOMS, json={"title": "Otra"}, headers=bea).json()["id"]
    submission_id = _explain(client, room_id, ana)

    assert _review(client, other, submission_id, bea).status_code == 404
    assert client.post(f"{ROOMS}/{other}/teachback/{submission_id}/ai-feedback", headers=bea).status_code == 404


def test_full_cycle_peer_review_then_ai(client, room_id, ana, bea, deepseek):
    calls, state = deepseek
    state["response"] = completion(FEEDBACK)
    submission_id = _explain(client, room_id, ana)
    assert _review(client, room_id, submission_id, bea).status_code == 201

    listed = client.get(f"{ROOMS}/{room_id}/teachback", headers=ana).json()
    response = client.post(f"{ROOMS}/{room_id}/teachback/{submission_id}/ai-feedback", headers=ana)

    assert listed[0]["review"]["comment"] == "He entendido la reserva"
    assert listed[0]["review"]["reviewerName"] == "Bea Privada"
    assert response.status_code == 200
    assert response.json()["questionsForPeer"] == FEEDBACK["questions_for_peer"]
    assert "improvedExplanation" not in response.json()
    assert "score" not in response.json()
    sent = json.dumps(calls[-1], ensure_ascii=False)
    assert "He entendido la reserva" in sent
    for private in ("Ana Privada", "Bea Privada", "privada@hack4edu.org", KEY):
        assert private not in sent


@pytest.mark.parametrize(
    "response",
    [completion("no es JSON"), completion({**FEEDBACK, "strengths": "no es una lista"}), completion({**FEEDBACK, "strengths": ["x"] * 6})],
)
def test_invalid_feedback_is_a_clear_error_and_keeps_the_review(client, room_id, ana, bea, deepseek, response):
    _, state = deepseek
    state["response"] = response
    submission_id = _explain(client, room_id, ana)
    _review(client, room_id, submission_id, bea)

    result = client.post(f"{ROOMS}/{room_id}/teachback/{submission_id}/ai-feedback", headers=ana)

    assert result.status_code == 503
    assert client.get(f"{ROOMS}/{room_id}/teachback", headers=ana).json()[0]["review"] is not None


def test_feedback_without_key_is_a_clear_error(client, room_id, ana, bea):
    submission_id = _explain(client, room_id, ana)
    _review(client, room_id, submission_id, bea)

    assert client.post(f"{ROOMS}/{room_id}/teachback/{submission_id}/ai-feedback", headers=ana).status_code == 503
