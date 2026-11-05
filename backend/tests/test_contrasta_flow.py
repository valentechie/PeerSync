"""Recorrido por parejas: privacidad, permisos, consentimiento e IA a petición."""

import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.ai import deepseek_client
from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.models.session import ComparisonStatus, ContrastaComparison, ContrastaRound
from conftest import join_room

ROOMS = "/api/rooms"
KEY = "clave-de-prueba"
SECRET_A = "RESPUESTA-SECRETA-DE-ANA"
SECRET_B = "RESPUESTA-SECRETA-DE-LUIS"
COMPARISON = {
    "agreements": ["Both discuss the pointer"],
    "differences": [],
    "questions": ["What changes in memory?"],
    "claims_to_verify": ["p++ moves the pointer"],
    "uncertainty_note": "This may be wrong.",
}
HELP = {"message": "What is p?", "suggested_action": "Write a tiny test.", "uncertainty_note": "Not verified."}
FEEDBACK = {
    "strengths": ["Clear"],
    "possible_gaps": [],
    "questions_for_peer": [],
    "evidence_to_check": [],
    "suggested_peer_activity": "Swap examples.",
    "uncertainty_note": "May be wrong.",
}


@pytest.fixture
def deepseek(monkeypatch):
    calls = []
    state = {"content": COMPARISON, "error": None}

    def fake_post(url, headers, json, timeout):
        calls.append(json)
        if state["error"]:
            raise state["error"]
        body = {"choices": [{"message": {"content": _dumps(state["content"])}}]}
        return httpx.Response(200, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr(deepseek_client.httpx, "post", fake_post)
    monkeypatch.setattr(get_settings(), "deepseek_api_key", KEY)
    return calls, state


def _dumps(value):
    return json.dumps(value)


@pytest.fixture
def ana(auth_headers):
    return auth_headers(email="ana.flujo@hack4edu.org", name="Ana Nombre")


@pytest.fixture
def luis(auth_headers):
    return auth_headers(email="luis.flujo@hack4edu.org", name="Luis Nombre")


@pytest.fixture
def eva(auth_headers):
    return auth_headers(email="eva.flujo@hack4edu.org", name="Eva Nombre")


def _user_id(client, headers):
    return client.get("/api/profiles/me", headers=headers).json()["id"]


@pytest.fixture
def room_id(client, ana, luis):
    id_ = client.post(ROOMS, json={"title": "Punteros", "objective": "p++"}, headers=ana).json()["id"]
    assert join_room(client, id_, luis).status_code == 200
    return id_


def _url(room_id, path=""):
    return f"{ROOMS}/{room_id}/contrasta{path}"


def _flow(client, room_id, headers):
    response = client.get(_url(room_id, "/flow"), headers=headers)
    assert response.status_code == 200
    return response.json()


def _start(client, room_id, ana, luis):
    response = client.post(
        _url(room_id, "/rounds"), json={"prompt": "p++ vs (*p)++", "partnerId": _user_id(client, luis)}, headers=ana
    )
    assert response.status_code == 201
    return response.json()["round"]


def _revealed(client, room_id, ana, luis):
    _start(client, room_id, ana, luis)
    assert client.post(_url(room_id, "/answers"), json={"answer": SECRET_A}, headers=ana).status_code == 201
    assert client.post(_url(room_id, "/answers"), json={"answer": SECRET_B}, headers=luis).status_code == 201


def _action(flow, key):
    return next(action for action in flow["actions"] if action["key"] == key)


def _active_activity(client, room_id, ana, luis):
    _revealed(client, room_id, ana, luis)
    client.post(_url(room_id, "/activities"), json={"concept": "Pointers"}, headers=ana)
    activity_id = _flow(client, room_id, luis)["activities"][0]["id"]
    assert client.post(_url(room_id, f"/activities/{activity_id}/respond/accept"), headers=luis).status_code == 200
    return activity_id


def _turn(client, room_id, activity_id, explainer, reviewer):
    assert client.post(_url(room_id, f"/activities/{activity_id}/explanation"), json={"explanation": "Mine"}, headers=explainer).status_code == 200
    assert client.post(_url(room_id, f"/activities/{activity_id}/review"), json={"comment": "Ok"}, headers=reviewer).status_code == 200


# Privacidad de las respuestas


def test_partner_answer_is_in_no_endpoint_before_both_answer(client, room_id, ana, luis):
    _start(client, room_id, ana, luis)
    client.post(_url(room_id, "/answers"), json={"answer": SECRET_A}, headers=ana)
    for path in ("/flow", ""):
        assert SECRET_A not in client.get(_url(room_id, path), headers=luis).text
    flow = _flow(client, room_id, luis)
    assert flow["round"]["partnerHasAnswered"] is True
    assert flow["round"]["answers"] == []
    assert flow["round"]["myAnswer"] is None
    assert _flow(client, room_id, ana)["round"]["myAnswer"] == SECRET_A


def test_reveals_automatically_without_calling_the_ai(client, room_id, ana, luis, deepseek):
    calls, _ = deepseek
    _revealed(client, room_id, ana, luis)
    for headers in (ana, luis):
        round_ = _flow(client, room_id, headers)["round"]
        assert round_["status"] == "revealed"
        assert {answer["answer"] for answer in round_["answers"]} == {SECRET_A, SECRET_B}
    assert calls == []


def test_third_person_never_sees_the_pair_content(client, room_id, ana, luis, eva, deepseek):
    assert join_room(client, room_id, eva).status_code == 200
    _revealed(client, room_id, ana, luis)
    assert client.post(_url(room_id, "/comparison"), headers=ana).status_code == 200
    for path in ("/flow", ""):
        text = client.get(_url(room_id, path), headers=eva).text
        assert SECRET_A not in text and SECRET_B not in text and "Both discuss" not in text
    flow = _flow(client, room_id, eva)
    assert flow["round"] is None and flow["otherPairInProgress"] is True
    assert all(action["enabled"] is False for action in flow["actions"])


def test_third_person_cannot_act_on_the_round(client, room_id, ana, luis, eva, deepseek):
    calls, _ = deepseek
    assert join_room(client, room_id, eva).status_code == 200
    _start(client, room_id, ana, luis)
    assert client.post(_url(room_id, "/answers"), json={"answer": "x"}, headers=eva).status_code == 403
    for path, body in (("/help", {"kind": "hint", "text": "x"}), ("/comparison", None), ("/round/cancel", None)):
        assert client.post(_url(room_id, path), json=body, headers=eva).status_code == 403
    assert calls == []


def test_room_membership_changes_do_not_reveal(client, room_id, ana, luis, eva):
    assert join_room(client, room_id, eva).status_code == 200
    _start(client, room_id, ana, luis)
    client.post(_url(room_id, "/answers"), json={"answer": SECRET_A}, headers=ana)
    assert client.post(f"{ROOMS}/{room_id}/leave", headers=luis).status_code == 200
    assert client.post(f"{ROOMS}/{room_id}/leave", headers=eva).status_code == 200
    assert _flow(client, room_id, ana)["round"]["status"] == "individual"


def test_cancelled_round_never_reveals(client, room_id, ana, luis):
    _start(client, room_id, ana, luis)
    client.post(_url(room_id, "/answers"), json={"answer": SECRET_A}, headers=ana)
    assert client.post(_url(room_id, "/round/cancel"), headers=luis).status_code == 200
    flow = _flow(client, room_id, luis)
    assert SECRET_A not in json.dumps(flow)
    assert client.post(_url(room_id, "/answers"), json={"answer": SECRET_B}, headers=luis).status_code == 409
    assert _action(flow, "start")["enabled"] is True


def test_partner_must_be_someone_else_in_the_room(client, room_id, ana, eva):
    for partner in (_user_id(client, ana), _user_id(client, eva)):
        response = client.post(_url(room_id, "/rounds"), json={"prompt": "x", "partnerId": partner}, headers=ana)
        assert response.status_code == 422


# Menú


def test_menu_follows_the_round_state(client, room_id, ana, luis):
    assert [a["key"] for a in _flow(client, room_id, ana)["actions"]] == ["start"]
    _start(client, room_id, ana, luis)
    flow = _flow(client, room_id, ana)
    assert [a["key"] for a in flow["actions"]] == ["hint", "idea", "practice", "conclusion"]
    assert _action(flow, "hint")["enabled"] is True
    assert _action(flow, "practice")["reason"] == "Available after the reveal"
    client.post(_url(room_id, "/answers"), json={"answer": "a"}, headers=ana)
    client.post(_url(room_id, "/answers"), json={"answer": "b"}, headers=luis)
    assert all(a["enabled"] for a in _flow(client, room_id, ana)["actions"])


def test_alone_in_the_room_is_told_to_invite(client, auth_headers):
    solo = auth_headers(email="solo@hack4edu.org", name="Solo")
    id_ = client.post(ROOMS, json={"title": "Sola", "objective": ""}, headers=solo).json()["id"]
    assert _flow(client, id_, solo)["actions"] == [{"key": "start", "enabled": False, "reason": "Invite someone first"}]


def test_no_second_round_while_one_is_active_and_a_new_one_after_finishing(client, room_id, ana, luis):
    _revealed(client, room_id, ana, luis)
    body = {"prompt": "Otra", "partnerId": _user_id(client, luis)}
    assert client.post(_url(room_id, "/rounds"), json=body, headers=ana).status_code == 409
    # La ruta antigua tampoco puede sustituir una ronda de pareja activa.
    assert client.post(_url(room_id, "/rounds"), json={"prompt": "Otra"}, headers=ana).status_code == 409
    assert client.post(_url(room_id, "/round/finish"), headers=ana).status_code == 200
    assert _flow(client, room_id, ana)["round"]["finishedAt"] is None
    assert client.post(_url(room_id, "/round/finish"), headers=luis).status_code == 200
    assert _flow(client, room_id, ana)["round"]["finishedAt"] is not None
    assert client.post(_url(room_id, "/rounds"), json=body, headers=ana).status_code == 201


def test_old_revealed_round_offers_a_new_round(client, room_id, ana, luis):
    client.post(_url(room_id, "/rounds"), json={"prompt": "Antigua"}, headers=ana)
    client.post(_url(room_id, "/answers"), json={"answer": "a"}, headers=ana)
    assert _action(_flow(client, room_id, luis), "start")["enabled"] is False
    client.post(_url(room_id, "/answers"), json={"answer": "b"}, headers=luis)
    assert _action(_flow(client, room_id, ana), "start")["enabled"] is True


# Comparación con IA


def test_comparison_needs_the_reveal_and_no_ai_runs_before(client, room_id, ana, luis, deepseek):
    calls, _ = deepseek
    _start(client, room_id, ana, luis)
    client.post(_url(room_id, "/answers"), json={"answer": SECRET_A}, headers=ana)
    assert client.post(_url(room_id, "/comparison"), headers=ana).status_code == 409
    assert calls == []


def test_comparison_is_minimal_shared_and_only_once(client, room_id, ana, luis, deepseek):
    calls, _ = deepseek
    _revealed(client, room_id, ana, luis)
    client.post(f"{ROOMS}/{room_id}/messages", json={"content": "CHAT-PRIVADO"}, headers=ana)
    assert client.post(_url(room_id, "/comparison"), headers=ana).status_code == 200
    assert client.post(_url(room_id, "/comparison"), headers=luis).status_code == 200
    assert len(calls) == 1
    sent = json.dumps(calls[0]["messages"][1])
    assert SECRET_A in sent and SECRET_B in sent
    for private in ("Ana Nombre", "Luis Nombre", "hack4edu.org", "CHAT-PRIVADO"):
        assert private not in sent
    for headers in (ana, luis):
        flow = _flow(client, room_id, headers)
        assert flow["comparison"]["status"] == "ready"
        assert flow["comparison"]["result"]["questions"] == ["What changes in memory?"]
        assert {answer["answer"] for answer in flow["round"]["answers"]} == {SECRET_A, SECRET_B}


def test_comparison_has_no_score_fields_even_if_the_model_sends_them(client, room_id, ana, luis, deepseek):
    _, state = deepseek
    state["content"] = {**COMPARISON, "winner": "Student A", "score": 9}
    _revealed(client, room_id, ana, luis)
    client.post(_url(room_id, "/comparison"), headers=ana)
    text = client.get(_url(room_id, "/flow"), headers=ana).text
    assert "winner" not in text and '"score"' not in text


def test_prompt_forbids_verdicts():
    from app.ai.contrasta.facilitator import COMPARE_PROMPT

    assert "Never decide who is right" in COMPARE_PROMPT
    assert "never invent disagreements" in COMPARE_PROMPT


def test_comparison_failure_is_recoverable_and_chat_keeps_working(client, room_id, ana, luis, deepseek):
    calls, state = deepseek
    state["error"] = httpx.ConnectError("sin red")
    _revealed(client, room_id, ana, luis)
    assert client.post(_url(room_id, "/comparison"), headers=ana).status_code == 503
    assert _flow(client, room_id, luis)["comparison"]["status"] == "failed"
    assert client.post(f"{ROOMS}/{room_id}/messages", json={"content": "Seguimos"}, headers=luis).status_code == 201
    state["error"] = None
    assert client.post(_url(room_id, "/comparison"), headers=luis).status_code == 200
    assert _flow(client, room_id, ana)["comparison"]["status"] == "ready"
    assert len(calls) == 2


def test_stale_pending_comparison_can_be_retried(client, room_id, ana, luis, deepseek):
    calls, _ = deepseek
    _revealed(client, room_id, ana, luis)
    with next(app.dependency_overrides[get_db]()) as session:
        round_ = session.query(ContrastaRound).one()
        session.add(
            ContrastaComparison(
                round_id=round_.id, status=ComparisonStatus.PENDING, updated_at=datetime.now(timezone.utc) - timedelta(minutes=5)
            )
        )
        session.commit()
    assert client.post(_url(room_id, "/comparison"), headers=luis).status_code == 200
    assert len(calls) == 1
    assert _flow(client, room_id, ana)["comparison"]["status"] == "ready"


def test_recent_pending_comparison_does_not_call_again(client, room_id, ana, luis, deepseek):
    calls, _ = deepseek
    _revealed(client, room_id, ana, luis)
    with next(app.dependency_overrides[get_db]()) as session:
        round_ = session.query(ContrastaRound).one()
        session.add(ContrastaComparison(round_id=round_.id, status=ComparisonStatus.PENDING, updated_at=datetime.now(timezone.utc)))
        session.commit()
    assert client.post(_url(room_id, "/comparison"), headers=luis).status_code == 200
    assert calls == []


# StudyMind


def test_hint_before_reveal_is_private_and_without_answers(client, room_id, ana, luis, deepseek):
    calls, state = deepseek
    state["content"] = HELP
    _start(client, room_id, ana, luis)
    client.post(_url(room_id, "/answers"), json={"answer": SECRET_B}, headers=luis)
    assert client.post(_url(room_id, "/help"), json={"kind": "hint", "text": "MI-DUDA"}, headers=ana).status_code == 200
    sent = json.dumps(calls[0]["messages"])
    assert SECRET_B not in sent and "Luis Nombre" not in sent
    assert "Do not suggest talking to" in calls[0]["messages"][0]["content"]
    assert len(_flow(client, room_id, ana)["cards"]) == 1
    assert "MI-DUDA" not in client.get(_url(room_id, "/flow"), headers=luis).text


def test_hint_after_reveal_is_shared(client, room_id, ana, luis, deepseek):
    _, state = deepseek
    state["content"] = HELP
    _revealed(client, room_id, ana, luis)
    client.post(_url(room_id, "/help"), json={"kind": "hint", "text": "Duda"}, headers=ana)
    assert _flow(client, room_id, luis)["cards"][0]["result"]["message"] == "What is p?"


def test_idea_check_needs_the_reveal_and_never_claims_results(client, room_id, ana, luis, deepseek):
    calls, state = deepseek
    state["content"] = HELP
    _start(client, room_id, ana, luis)
    assert client.post(_url(room_id, "/help"), json={"kind": "idea", "text": "x"}, headers=ana).status_code == 409
    client.post(_url(room_id, "/answers"), json={"answer": "a"}, headers=ana)
    client.post(_url(room_id, "/answers"), json={"answer": "b"}, headers=luis)
    assert client.post(_url(room_id, "/help"), json={"kind": "idea", "text": "x"}, headers=ana).status_code == 200
    assert "Never claim a result" in calls[0]["messages"][0]["content"]


def test_help_failure_is_a_recoverable_error_not_prepared_text(client, room_id, ana, luis, deepseek):
    _, state = deepseek
    state["error"] = httpx.ConnectError("sin red")
    _revealed(client, room_id, ana, luis)
    assert client.post(_url(room_id, "/help"), json={"kind": "hint", "text": "x"}, headers=ana).status_code == 503
    assert _flow(client, room_id, ana)["cards"] == []


# Propuesta y actividad TeachBack


def test_proposal_needs_the_partner_and_does_not_block_the_chat(client, room_id, ana, luis):
    _revealed(client, room_id, ana, luis)
    client.post(_url(room_id, "/activities"), json={"concept": "Punteros"}, headers=ana)
    activity = _flow(client, room_id, luis)["activities"][0]
    assert activity["status"] == "pending"
    assert client.post(f"{ROOMS}/{room_id}/messages", json={"content": "Hola"}, headers=luis).status_code == 201
    accept = _url(room_id, f"/activities/{activity['id']}/respond/accept")
    assert client.post(accept, headers=ana).status_code == 403
    explain = _url(room_id, f"/activities/{activity['id']}/explanation")
    assert client.post(explain, json={"explanation": "x"}, headers=ana).status_code == 409
    assert client.post(_url(room_id, f"/activities/{activity['id']}/respond/decline"), headers=luis).status_code == 200
    assert _flow(client, room_id, ana)["activities"][0]["status"] == "declined"
    assert _action(_flow(client, room_id, ana), "practice")["enabled"] is True


def test_double_accept_and_double_proposal_do_not_duplicate(client, room_id, ana, luis):
    _revealed(client, room_id, ana, luis)
    for headers in (ana, luis, ana):
        assert client.post(_url(room_id, "/activities"), json={"concept": "P"}, headers=headers).status_code == 200
    flow = _flow(client, room_id, luis)
    assert len(flow["activities"]) == 1
    accept = _url(room_id, f"/activities/{flow['activities'][0]['id']}/respond/accept")
    assert client.post(accept, headers=luis).status_code == 200
    assert client.post(accept, headers=luis).status_code == 200
    assert len(_flow(client, room_id, ana)["activities"]) == 1


def test_full_activity_with_roles_and_ai_only_after_review(client, room_id, ana, luis, deepseek):
    calls, state = deepseek
    state["content"] = FEEDBACK
    activity_id = _active_activity(client, room_id, ana, luis)
    base = f"/activities/{activity_id}"
    assert client.post(_url(room_id, base + "/explanation"), json={"explanation": "x"}, headers=luis).status_code == 409
    assert client.post(_url(room_id, base + "/explanation"), json={"explanation": "Mine"}, headers=ana).status_code == 200
    assert client.post(_url(room_id, base + "/feedback"), json={"turn": 1}, headers=ana).status_code == 409
    assert calls == []
    assert client.post(_url(room_id, base + "/review"), json={"comment": "x"}, headers=ana).status_code == 409
    assert client.post(_url(room_id, base + "/advance"), headers=ana).status_code == 409
    assert client.post(_url(room_id, base + "/review"), json={"comment": "Ok"}, headers=luis).status_code == 200
    assert client.post(_url(room_id, base + "/feedback"), json={"turn": 1}, headers=ana).status_code == 200
    assert client.post(_url(room_id, base + "/feedback"), json={"turn": 1}, headers=luis).status_code == 200
    assert len(calls) == 1
    assert "Ana Nombre" not in json.dumps(calls[0]["messages"])
    assert _flow(client, room_id, luis)["activities"][0]["turns"][0]["feedback"]["strengths"] == ["Clear"]
    assert client.post(_url(room_id, base + "/advance"), headers=luis).status_code == 200
    assert _flow(client, room_id, ana)["activities"][0]["turn"] == 2
    _turn(client, room_id, activity_id, luis, ana)
    assert client.post(_url(room_id, base + "/advance"), headers=ana).status_code == 200
    flow = _flow(client, room_id, luis)
    assert flow["activities"][0]["status"] == "completed"
    assert flow["suggestion"]["key"] == "check"
    assert client.post(f"{ROOMS}/{room_id}/messages", json={"content": "Fin"}, headers=luis).status_code == 201


def test_second_turn_is_skipped_only_if_both_agree(client, room_id, ana, luis):
    activity_id = _active_activity(client, room_id, ana, luis)
    _turn(client, room_id, activity_id, ana, luis)
    skip = _url(room_id, f"/activities/{activity_id}/skip")
    assert client.post(skip, headers=ana).status_code == 200
    assert client.post(skip, headers=ana).status_code == 200
    assert _flow(client, room_id, luis)["activities"][0]["status"] == "active"
    assert client.post(skip, headers=luis).status_code == 200
    assert _flow(client, room_id, ana)["activities"][0]["status"] == "completed"


def test_activity_can_be_left_and_blocks_finishing_only_while_active(client, room_id, ana, luis):
    activity_id = _active_activity(client, room_id, ana, luis)
    assert client.post(_url(room_id, "/round/finish"), headers=ana).status_code == 409
    assert client.post(_url(room_id, f"/activities/{activity_id}/leave"), headers=luis).status_code == 200
    assert client.post(_url(room_id, "/round/finish"), headers=ana).status_code == 200


def test_activity_turns_stay_out_of_the_independent_panel(client, room_id, ana, luis, eva):
    assert join_room(client, room_id, eva).status_code == 200
    activity_id = _active_activity(client, room_id, ana, luis)
    client.post(_url(room_id, f"/activities/{activity_id}/explanation"), json={"explanation": "Solo pareja"}, headers=ana)
    assert client.get(f"{ROOMS}/{room_id}/teachback", headers=eva).json() == []
    assert "Solo pareja" not in client.get(_url(room_id, "/flow"), headers=eva).text


def test_activity_of_another_round_is_not_reachable(client, room_id, ana, luis):
    activity_id = _active_activity(client, room_id, ana, luis)
    assert client.post(_url(room_id, f"/activities/{activity_id}/leave"), headers=ana).status_code == 200
    client.post(_url(room_id, "/round/finish"), headers=ana)
    client.post(_url(room_id, "/round/finish"), headers=luis)
    # SQLite solo guarda segundos: sin esto, las dos rondas empatarían como la más reciente.
    with next(app.dependency_overrides[get_db]()) as session:
        session.query(ContrastaRound).update({"created_at": datetime.now(timezone.utc) - timedelta(hours=1)})
        session.commit()
    _start(client, room_id, ana, luis)
    client.post(_url(room_id, "/answers"), json={"answer": "a"}, headers=ana)
    client.post(_url(room_id, "/answers"), json={"answer": "b"}, headers=luis)
    assert client.post(_url(room_id, f"/activities/{activity_id}/leave"), headers=ana).status_code == 404


def test_independent_teachback_still_works_during_a_round(client, room_id, ana, luis):
    _start(client, room_id, ana, luis)
    created = client.post(f"{ROOMS}/{room_id}/teachback", json={"concept": "C", "explanation": "E"}, headers=ana)
    assert created.status_code == 201
    review = client.post(f"{ROOMS}/{room_id}/teachback/{created.json()['id']}/review", json={"comment": "Ok"}, headers=luis)
    assert review.status_code == 201


# Conclusión y sugerencias


def test_conclusion_is_confirmed_by_the_partner_and_suggests_teachback(client, room_id, ana, luis):
    _revealed(client, room_id, ana, luis)
    assert _flow(client, room_id, ana)["suggestion"] is None
    assert client.post(_url(room_id, "/conclusion"), json={"text": "Acuerdo"}, headers=ana).status_code == 200
    flow = _flow(client, room_id, luis)
    assert flow["round"]["conclusion"]["text"] == "Acuerdo"
    assert flow["suggestion"]["key"] == "teachback"
    assert client.post(_url(room_id, "/conclusion/confirm"), headers=ana).status_code == 409
    assert client.post(_url(room_id, "/conclusion/confirm"), headers=luis).status_code == 200
    assert _action(_flow(client, room_id, ana), "conclusion")["reason"] == "Already recorded"
    # TeachBack no es obligatorio: se puede finalizar sin hacerlo.
    assert client.post(_url(room_id, "/round/finish"), headers=ana).status_code == 200
    assert client.post(_url(room_id, "/round/finish"), headers=luis).status_code == 200


def test_suggestion_disappears_once_the_pair_proposes(client, room_id, ana, luis):
    _revealed(client, room_id, ana, luis)
    client.post(_url(room_id, "/conclusion"), json={"text": "Acuerdo"}, headers=ana)
    client.post(_url(room_id, "/activities"), json={"concept": "P"}, headers=luis)
    assert _flow(client, room_id, ana)["suggestion"] is None


# Comprobación individual


def test_check_answers_are_hidden_until_both_and_have_no_grade(client, room_id, ana, luis):
    _revealed(client, room_id, ana, luis)
    assert client.post(_url(room_id, "/check"), json={"question": "¿Y con q?"}, headers=ana).status_code == 200
    assert client.post(_url(room_id, "/check/answer"), json={"answer": "CHECK-ANA"}, headers=ana).status_code == 200
    assert "CHECK-ANA" not in client.get(_url(room_id, "/flow"), headers=luis).text
    assert client.post(_url(room_id, "/check/answer"), json={"answer": "x"}, headers=ana).status_code == 409
    client.post(_url(room_id, "/check/answer"), json={"answer": "CHECK-LUIS", "reflection": "Cambió"}, headers=luis)
    check = _flow(client, room_id, ana)["check"]
    assert check["source"] == "peer"
    assert [a["answer"] for a in check["answers"]] == ["CHECK-ANA", "CHECK-LUIS"]
    assert set(check["answers"][0]) == {"person", "answer", "reflection"}


def test_ai_check_question_is_labelled_and_can_fail(client, room_id, ana, luis, deepseek):
    calls, state = deepseek
    state["error"] = httpx.ConnectError("sin red")
    _revealed(client, room_id, ana, luis)
    assert client.post(_url(room_id, "/check"), json={}, headers=ana).status_code == 503
    state["error"] = None
    state["content"] = {"question": "What about q?"}
    assert client.post(_url(room_id, "/check"), json={}, headers=ana).status_code == 200
    check = _flow(client, room_id, luis)["check"]
    assert check["source"] == "ai" and check["question"] == "What about q?"
    assert SECRET_A not in json.dumps(calls[-1]["messages"])


# Sala


def test_outsider_and_closed_room(client, room_id, ana, luis, eva):
    assert client.get(_url(room_id, "/flow"), headers=eva).status_code == 403
    _start(client, room_id, ana, luis)
    client.post(f"{ROOMS}/{room_id}/leave", headers=ana)
    client.post(f"{ROOMS}/{room_id}/leave", headers=luis)
    assert client.post(_url(room_id, "/round/cancel"), headers=ana).status_code in (403, 409)


def test_room_without_round_keeps_working(client, room_id, ana):
    flow = _flow(client, room_id, ana)
    assert flow["round"] is None
    assert client.post(f"{ROOMS}/{room_id}/messages", json={"content": "Hola"}, headers=ana).status_code == 201
