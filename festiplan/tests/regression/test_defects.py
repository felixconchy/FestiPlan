"""Tests de non-régression des trois défauts initiaux.

Ils passent par l'API HTTP pour reproduire exactement les scénarios décrits dans
le sujet. Ils ont été écrits AVANT la correction (marqués xfail) puis
débloqués au fur et à mesure des corrections.
"""
import pytest

from app.config import settings


def _post(client, url, payload):
    r = client.post(url, json=payload)
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
def planning(client):
    """Un festival, deux scènes, deux artistes et deux concerts sur la Mainstage."""
    festival = _post(client, "/festivals", {
        "name": "Hellforge Open Air", "location": "Clisson",
        "start_date": "2027-06-18T10:00:00", "end_date": "2027-06-20T23:59:00",
    })
    main = _post(client, "/stages", {"festival_id": festival["id"], "name": "Mainstage", "capacity": 50000,
                                     "available_equipment": ["special_lighting"]})
    warzone = _post(client, "/stages", {"festival_id": festival["id"], "name": "Warzone", "capacity": 15000,
                                        "available_equipment": ["special_lighting"]})
    iron = _post(client, "/artists", {"name": "Iron Vow", "genre": "Heavy", "required_equipment": []})
    crimson = _post(client, "/artists", {"name": "Crimson Engine", "genre": "Thrash", "required_equipment": []})
    c1 = _post(client, "/concerts", {"festival_id": festival["id"], "artist_id": iron["id"], "stage_id": main["id"],
                                     "start_time": "2027-06-18T18:00:00", "end_time": "2027-06-18T19:00:00"})
    c2 = _post(client, "/concerts", {"festival_id": festival["id"], "artist_id": crimson["id"], "stage_id": main["id"],
                                     "start_time": "2027-06-18T20:00:00", "end_time": "2027-06-18T21:00:00"})
    return {"festival": festival, "main": main, "warzone": warzone, "iron": iron, "crimson": crimson,
            "c1": c1, "c2": c2}


# --- Défaut 1 : chevauchement de concerts -------------------------------------------------

def test_defect1_reschedule_onto_occupied_stage_is_refused(client, planning):
    c2 = planning["c2"]
    r = client.patch(f"/concerts/{c2['id']}/reschedule",
                     json={"start_time": "2027-06-18T18:30:00", "end_time": "2027-06-18T19:30:00"})
    assert r.status_code == 409
    # le concert n'a pas bougé
    assert client.get(f"/concerts/{c2['id']}").json()["start_time"] == "2027-06-18T20:00:00"


def test_defect1_artist_cannot_play_on_two_stages_at_once(client, planning):
    p = planning
    c3 = _post(client, "/concerts", {"festival_id": p["festival"]["id"], "artist_id": p["iron"]["id"],
                                     "stage_id": p["warzone"]["id"],
                                     "start_time": "2027-06-19T18:00:00", "end_time": "2027-06-19T19:00:00"})
    r = client.patch(f"/concerts/{c3['id']}/reschedule",
                     json={"start_time": "2027-06-18T18:30:00", "end_time": "2027-06-18T19:30:00"})
    assert r.status_code == 409


def test_defect1_valid_reschedule_is_accepted(client, planning):
    c2 = planning["c2"]
    r = client.patch(f"/concerts/{c2['id']}/reschedule",
                     json={"start_time": "2027-06-18T21:00:00", "end_time": "2027-06-18T22:00:00"})
    assert r.status_code == 200
    assert r.json()["start_time"] == "2027-06-18T21:00:00"


# --- Défaut 2 : échec de notification après modification ----------------------------------

def test_defect2_notification_failure_does_not_hide_successful_change(client, planning, monkeypatch):
    monkeypatch.setattr(settings, "fail_notifications", True)
    c2 = planning["c2"]
    r = client.patch(f"/concerts/{c2['id']}/reschedule",
                     json={"start_time": "2027-06-18T21:00:00", "end_time": "2027-06-18T22:00:00"})
    assert r.status_code == 200
    assert r.json()["notification_status"] == "failed"
    assert client.get(f"/concerts/{c2['id']}").json()["start_time"] == "2027-06-18T21:00:00"


# --- Défaut 3 : modification d'un planning publié ------------------------------------------

def test_defect3_ordinary_reschedule_refused_once_published(client, planning):
    assert client.post(f"/festivals/{planning['festival']['id']}/publish").status_code == 200
    c2 = planning["c2"]
    r = client.patch(f"/concerts/{c2['id']}/reschedule",
                     json={"start_time": "2027-06-18T21:00:00", "end_time": "2027-06-18T22:00:00"})
    assert r.status_code == 409
    assert client.get(f"/concerts/{c2['id']}").json()["start_time"] == "2027-06-18T20:00:00"


def test_defect3_explicit_procedure_allows_change_of_published_schedule(client, planning):
    assert client.post(f"/festivals/{planning['festival']['id']}/publish").status_code == 200
    c2 = planning["c2"]
    r = client.post(f"/concerts/{c2['id']}/published-reschedule",
                    json={"start_time": "2027-06-18T21:00:00", "end_time": "2027-06-18T22:00:00",
                          "reason": "Retard de transport du groupe"})
    assert r.status_code == 200
    assert r.json()["start_time"] == "2027-06-18T21:00:00"
    festival = client.get("/festivals").json()[0]
    assert festival["status"] == "published"
