from uuid import UUID

import pytest

from app.ai.skillswap.connections import connection_score, connection_strength
from app.ai.skillswap.studies import StudyRelation
from app.core.database import get_db
from app.main import app
from app.models.user import User
from app.services import connection_service
from conftest import join_room

FRIENDS_GRAPH = "/api/connections/friends"
SUGGESTIONS = "/api/connections/suggestions"
FRIENDS = "/api/friends"
ME = "/api/profiles/me"


@pytest.fixture
def person(client, auth_headers):
    def _create(name, study=None, interests=()):
        headers = auth_headers(email=f"{name.lower()}@hack4edu.org", name=name)
        changes = {}
        if study:
            changes["studyCode"] = study
        if interests:
            changes["skillsSeeking"] = list(interests)
        if changes:
            assert client.patch(ME, json=changes, headers=headers).status_code == 200
        return headers, client.get(ME, headers=headers).json()["id"]

    return _create


@pytest.fixture
def befriend(client):
    def _befriend(first, first_id, second, second_id):
        client.post(f"{FRIENDS}/{second_id}", headers=first)
        assert client.post(f"{FRIENDS}/{first_id}/accept", headers=second).status_code == 200

    return _befriend


def _node(graph, name):
    return next(node for node in graph["nodes"] if node["name"] == name)


def _names(graph):
    return [node["name"] for node in graph["nodes"]]


def _peer_links(graph):
    return [link for link in graph["links"] if link["source"] != graph["me"]["id"]]


def test_score_rules_are_explainable():
    assert connection_score(None, 0, 0) == 0
    assert connection_score(StudyRelation.DIRECT, 0, 0) == 35
    assert connection_score(StudyRelation.SIMILAR, 0, 0) == 20
    assert connection_score(None, 2, 0) == 30
    assert connection_score(None, 0, 1) == 10
    # Los topes impiden que acumular temas o salas supere el máximo.
    assert connection_score(StudyRelation.DIRECT, 50, 50) == 100


def test_strength_thresholds():
    assert connection_strength(60) == "strong"
    assert connection_strength(59) == "good"
    assert connection_strength(35) == "good"
    assert connection_strength(34) == "possible"


def test_routes_require_a_token(client):
    assert client.get(FRIENDS_GRAPH).status_code == 401
    assert client.get(SUGGESTIONS).status_code == 401


def test_friends_graph_is_empty_without_friends(client, person):
    ana, ana_id = person("Ana")

    graph = client.get(FRIENDS_GRAPH, headers=ana).json()

    assert graph["me"] == {"id": ana_id, "name": "Ana", "photoUrl": None}
    assert graph["nodes"] == []
    assert graph["links"] == []


def test_friends_graph_has_all_accepted_friends_and_no_requests(client, person, befriend):
    ana, ana_id = person("Ana")
    bea, bea_id = person("Bea")
    _, carla_id = person("Carla")
    dani, _ = person("Dani")
    befriend(ana, ana_id, bea, bea_id)
    client.post(f"{FRIENDS}/{carla_id}", headers=ana)
    client.post(f"{FRIENDS}/{ana_id}", headers=dani)

    graph = client.get(FRIENDS_GRAPH, headers=ana).json()

    assert _names(graph) == ["Bea"]
    # Una amistad sin nada en común también se dibuja, con la línea más floja.
    assert graph["links"] == [{"source": ana_id, "target": bea_id, "weight": 0.0, "reasons": []}]


def test_friend_node_explains_the_relationship(client, person, befriend):
    ana, ana_id = person("Ana", study="daw", interests=["Python", "Cálculo"])
    bea, bea_id = person("Bea", study="daw", interests=["python"])
    befriend(ana, ana_id, bea, bea_id)
    room_id = client.post("/api/rooms", json={"title": "Repaso"}, headers=ana).json()["id"]
    join_room(client, room_id, bea)

    node = _node(client.get(FRIENDS_GRAPH, headers=ana).json(), "Bea")

    assert node["score"] == 35 + 15 + 10
    assert node["strength"] == "strong"
    assert node["friendStatus"] == "friend"
    assert node["rooms"] == [{"id": room_id, "title": "Repaso"}]
    assert node["reasons"] == [
        "You study the same thing",
        "You both want to learn: Python",
        "You're in the same room: Repaso",
    ]


def test_graph_exposes_no_private_fields(client, person, befriend):
    ana, ana_id = person("Ana", study="daw")
    bea, bea_id = person("Bea", study="daw")
    client.patch(ME, json={"bio": "texto privado de Bea"}, headers=bea)
    befriend(ana, ana_id, bea, bea_id)

    for url in (FRIENDS_GRAPH, SUGGESTIONS):
        body = client.get(url, headers=ana).text
        assert "@hack4edu.org" not in body
        assert "texto privado" not in body


def test_friendships_between_others_are_never_revealed(client, person, befriend):
    ana, ana_id = person("Ana")
    bea, bea_id = person("Bea")
    carla, carla_id = person("Carla")
    befriend(ana, ana_id, bea, bea_id)
    befriend(ana, ana_id, carla, carla_id)
    befriend(bea, bea_id, carla, carla_id)

    assert _peer_links(client.get(FRIENDS_GRAPH, headers=ana).json()) == []


def test_friends_of_friends_are_not_suggested(client, person, befriend):
    ana, ana_id = person("Ana")
    bea, bea_id = person("Bea")
    carla, carla_id = person("Carla")
    befriend(ana, ana_id, bea, bea_id)
    befriend(bea, bea_id, carla, carla_id)

    assert _names(client.get(SUGGESTIONS, headers=ana).json()) == []


def test_rooms_you_are_not_in_stay_hidden(client, person, befriend):
    ana, ana_id = person("Ana")
    bea, bea_id = person("Bea")
    carla, carla_id = person("Carla")
    befriend(ana, ana_id, bea, bea_id)
    befriend(ana, ana_id, carla, carla_id)
    room_id = client.post("/api/rooms", json={"title": "Sala secreta"}, headers=bea).json()["id"]
    join_room(client, room_id, carla)

    response = client.get(FRIENDS_GRAPH, headers=ana)

    assert "Sala secreta" not in response.text
    assert _peer_links(response.json()) == []
    assert _names(client.get(SUGGESTIONS, headers=ana).json()) == []


def test_topics_only_the_other_two_share_stay_hidden(client, person, befriend):
    ana, ana_id = person("Ana", interests=["Python"])
    bea, bea_id = person("Bea", interests=["Python", "Tema privado"])
    carla, carla_id = person("Carla", interests=["Python", "Tema privado"])
    befriend(ana, ana_id, bea, bea_id)
    befriend(ana, ana_id, carla, carla_id)

    response = client.get(FRIENDS_GRAPH, headers=ana)

    assert "Tema privado" not in response.text
    assert [link["reasons"] for link in _peer_links(response.json())] == [["They both want to learn: Python"]]


def test_peer_links_show_what_the_viewer_can_already_see(client, person, befriend):
    ana, ana_id = person("Ana")
    bea, bea_id = person("Bea", study="daw")
    carla, carla_id = person("Carla", study="dam")
    befriend(ana, ana_id, bea, bea_id)
    befriend(ana, ana_id, carla, carla_id)

    links = _peer_links(client.get(FRIENDS_GRAPH, headers=ana).json())

    assert [link["reasons"] for link in links] == [["Similar studies: Computing"]]
    assert links[0]["weight"] == 0.2


def test_peer_links_per_person_are_capped(client, person, befriend):
    ana, ana_id = person("Ana")
    for index in range(6):
        other, other_id = person(f"Amigo{index}", study="daw")
        befriend(ana, ana_id, other, other_id)

    links = _peer_links(client.get(FRIENDS_GRAPH, headers=ana).json())

    counts = {}
    for link in links:
        counts[link["source"]] = counts.get(link["source"], 0) + 1
        counts[link["target"]] = counts.get(link["target"], 0) + 1
    assert links
    assert max(counts.values()) <= 3


def test_suggestions_rank_by_what_you_have_in_common(client, person):
    ana, _ = person("Ana", study="daw", interests=["Python", "Cálculo"])
    person("Zoe", study="dam")
    person("Bea", study="daw", interests=["Python", "Cálculo"])
    person("Carla", interests=["Python"])
    person("Dani", study="medicina", interests=["Cocina"])
    person("Eva")

    graph = client.get(SUGGESTIONS, headers=ana).json()

    assert _names(graph) == ["Bea", "Zoe", "Carla"]
    assert _node(graph, "Bea")["score"] == 65
    assert _node(graph, "Bea")["strength"] == "strong"
    assert _node(graph, "Zoe")["reasons"] == ["Similar studies: Computing"]
    assert _node(graph, "Carla")["strength"] == "possible"


def test_suggestions_are_deterministic(client, person):
    ana, _ = person("Ana", study="daw")
    for name in ("Zoe", "Bea", "Carla", "Mar"):
        person(name, study="daw")

    first = client.get(SUGGESTIONS, headers=ana).json()
    second = client.get(SUGGESTIONS, headers=ana).json()

    assert first == second
    assert _names(first) == ["Bea", "Carla", "Mar", "Zoe"]


def test_suggestions_skip_yourself_and_friends_but_keep_requests(client, person, befriend):
    ana, ana_id = person("Ana", study="daw")
    bea, bea_id = person("Bea", study="daw")
    _, carla_id = person("Carla", study="daw")
    dani, _ = person("Dani", study="daw")
    befriend(ana, ana_id, bea, bea_id)
    client.post(f"{FRIENDS}/{carla_id}", headers=ana)
    client.post(f"{FRIENDS}/{ana_id}", headers=dani)

    graph = client.get(SUGGESTIONS, headers=ana).json()

    assert _names(graph) == ["Carla", "Dani"]
    assert _node(graph, "Carla")["friendStatus"] == "sent"
    assert _node(graph, "Dani")["friendStatus"] == "received"


def test_a_room_mate_is_suggested(client, person):
    ana, _ = person("Ana")
    bea, _ = person("Bea")
    room_id = client.post("/api/rooms", json={"title": "Repaso"}, headers=ana).json()["id"]
    join_room(client, room_id, bea)

    node = _node(client.get(SUGGESTIONS, headers=ana).json(), "Bea")

    assert node["score"] == 10
    assert node["reasons"] == ["You're in the same room: Repaso"]


def test_inactive_people_do_not_appear(client, person, befriend):
    ana, ana_id = person("Ana", study="daw")
    bea, bea_id = person("Bea", study="daw")
    carla, carla_id = person("Carla", study="daw")
    befriend(ana, ana_id, bea, bea_id)

    db = next(app.dependency_overrides[get_db]())
    for user_id in (bea_id, carla_id):
        db.get(User, UUID(user_id)).is_active = False
    db.commit()

    assert _names(client.get(FRIENDS_GRAPH, headers=ana).json()) == []
    assert _names(client.get(SUGGESTIONS, headers=ana).json()) == []


def test_suggestions_have_a_limit(client, person, monkeypatch):
    # Se baja el tope para no chocar con el límite de peticiones al crear usuarios.
    monkeypatch.setattr(connection_service, "MAX_SUGGESTIONS", 2)
    ana, _ = person("Ana", study="daw")
    for name in ("Bea", "Carla", "Dani"):
        person(name, study="daw")

    assert _names(client.get(SUGGESTIONS, headers=ana).json()) == ["Bea", "Carla"]
