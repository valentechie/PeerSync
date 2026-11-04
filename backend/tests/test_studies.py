import pytest

from app.ai.skillswap.studies import STUDIES, StudyRelation, codes_in_family, study_label, study_relation

ME = "/api/profiles/me"
MATCHES = "/api/people/study-matches"


@pytest.mark.parametrize(
    "first, second, expected",
    [
        ("smr", "smr", StudyRelation.DIRECT),
        ("smr", "asir", StudyRelation.SIMILAR),
        ("smr", "ing-informatica", StudyRelation.SIMILAR),
        ("ing-informatica", "smr", StudyRelation.SIMILAR),
        ("smr", "otros-informatica", StudyRelation.SIMILAR),
        ("otros-informatica", "otros-informatica", StudyRelation.SIMILAR),
        ("smr", "medicina", None),
        ("otros", "otros", None),
        ("smr", "otros", None),
        ("smr", None, None),
        (None, None, None),
        ("smr", "no-existe", None),
    ],
)
def test_study_relation(first, second, expected):
    assert study_relation(first, second) == expected


def test_catalog_is_consistent():
    assert all(study.code == code for code, study in STUDIES.items())
    assert "smr" in codes_in_family("Informática")
    assert codes_in_family(None) == []
    assert study_label("smr") == "Grado Medio · Sistemas Microinformáticos y Redes"
    assert study_label("otros-informatica") == "Otros estudios de Informática"
    assert study_label("no-existe") is None


@pytest.fixture
def student(client, auth_headers):
    def _create(name, study=None, interests=None):
        headers = auth_headers(email=f"{name.lower()}@hack4edu.org", name=name)
        body = {}
        if study is not None:
            body["studyCode"] = study
        if interests is not None:
            body["skillsSeeking"] = interests
        if body:
            assert client.patch(ME, json=body, headers=headers).status_code == 200
        return headers

    return _create


def test_routes_require_a_token(client):
    assert client.get("/api/studies").status_code == 401
    assert client.get(MATCHES).status_code == 401


def test_catalog_lists_families(client, student):
    response = client.get("/api/studies", headers=student("Ana"))

    assert response.status_code == 200
    families = {family["name"]: family["studies"] for family in response.json()}
    assert {"code": "smr", "label": "Grado Medio · Sistemas Microinformáticos y Redes"} in families["Informática"]
    assert {"code": "otros", "label": "Otros estudios"} in families["Otros"]


def test_profile_saves_changes_and_clears_study(client, student):
    ana = student("Ana")
    assert client.get(ME, headers=ana).json()["studyCode"] is None

    assert client.patch(ME, json={"studyCode": "smr"}, headers=ana).json()["studyCode"] == "smr"
    assert client.get(ME, headers=ana).json()["study"] == "Grado Medio · Sistemas Microinformáticos y Redes"

    assert client.patch(ME, json={"name": "Ana María"}, headers=ana).json()["studyCode"] == "smr"
    assert client.patch(ME, json={"studyCode": None}, headers=ana).json()["studyCode"] is None


def test_invented_study_is_rejected(client, student):
    assert client.patch(ME, json={"studyCode": "inventado"}, headers=student("Ana")).status_code == 422


def test_direct_matches_go_first_and_similar_are_explained(client, student):
    ana = student("Ana", "smr")
    student("Zoe", "smr")
    student("Bea", "ing-informatica")
    student("Carla", "daw")
    student("Dani", "medicina")
    student("Eva")

    response = client.get(MATCHES, headers=ana).json()

    assert [person["name"] for person in response] == ["Zoe", "Bea", "Carla"]
    assert [person["matchType"] for person in response] == ["direct", "similar", "similar"]
    assert response[0]["matchReason"] == "Estudiáis lo mismo"
    assert response[1]["matchReason"] == "Estudios parecidos: Informática"
    assert response[1]["study"] == "Universidad · Ingeniería Informática"


def test_shared_interests_break_ties_within_the_same_type(client, student):
    ana = student("Ana", "smr", ["Python", "Redes"])
    student("Alba", "smr")
    student("Zoe", "smr", ["python", "redes"])
    student("Bea", "asir", ["Python", "Redes"])

    response = client.get(MATCHES, headers=ana).json()

    assert [person["name"] for person in response] == ["Zoe", "Alba", "Bea"]
    assert response[0]["sharedInterests"] == ["Python", "Redes"]


def test_no_study_means_no_matches(client, student):
    student("Bea", "smr")

    assert client.get(MATCHES, headers=student("Ana")).json() == []


def test_generic_other_studies_do_not_match(client, student):
    ana = student("Ana", "otros")
    student("Bea", "otros")

    assert client.get(MATCHES, headers=ana).json() == []


def test_matches_exclude_yourself_and_expose_no_emails(client, student):
    ana = student("Ana", "smr")
    student("Bea", "smr")

    response = client.get(MATCHES, headers=ana)

    assert [person["name"] for person in response.json()] == ["Bea"]
    assert "hack4edu.org" not in response.text


def test_other_lists_show_the_study(client, student):
    ana = student("Ana", "smr")
    student("Bea", "daw")

    found = client.get("/api/people", params={"search": "bea"}, headers=ana).json()

    assert found[0]["study"] == "Grado Superior · Desarrollo de Aplicaciones Web"
