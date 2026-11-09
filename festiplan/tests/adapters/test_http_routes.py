"""Tests de l'adaptateur HTTP : routes, codes de statut et traduction des erreurs."""
import pytest


def post(client, url, payload, expected=201):
    r = client.post(url, json=payload)
    assert r.status_code == expected, r.text
    return r.json()


@pytest.fixture()
def base(client):
    f = post(client, "/festivals", {"name": "Hellforge", "location": "Clisson",
                                    "start_date": "2027-06-18T10:00:00", "end_date": "2027-06-20T23:59:00"})
    s = post(client, "/stages", {"festival_id": f["id"], "name": "Valley", "capacity": 8000,
                                 "available_equipment": ["special_lighting"]})
    a = post(client, "/artists", {"name": "Solar Funeral", "genre": "Doom", "required_equipment": []})
    c = post(client, "/concerts", {"festival_id": f["id"], "artist_id": a["id"], "stage_id": s["id"],
                                   "start_time": "2027-06-18T20:30:00", "end_time": "2027-06-18T21:30:00"})
    return f, s, a, c


def test_full_listing(client, base):
    f, s, a, c = base
    assert client.get("/festivals").json()[0]["status"] == "preparation"
    assert client.get("/stages", params={"festival_id": f["id"]}).json()[0]["available_equipment"] == ["special_lighting"]
    assert client.get("/artists").json()[0]["name"] == "Solar Funeral"
    assert client.get(f"/concerts/{c['id']}").json()["status"] == "scheduled"


def test_schedule_is_chronological_and_excludes_cancelled(client, base):
    f, s, a, _ = base
    early = post(client, "/concerts", {"festival_id": f["id"], "artist_id": a["id"], "stage_id": s["id"],
                                       "start_time": "2027-06-18T12:00:00", "end_time": "2027-06-18T13:00:00"})
    late = post(client, "/concerts", {"festival_id": f["id"], "artist_id": a["id"], "stage_id": s["id"],
                                      "start_time": "2027-06-19T12:00:00", "end_time": "2027-06-19T13:00:00"})
    assert client.post(f"/concerts/{late['id']}/cancel").json()["status"] == "cancelled"
    schedule = client.get(f"/concerts/schedule/{f['id']}").json()
    assert [x["id"] for x in schedule] == [early["id"], base[3]["id"]]
    assert client.get("/concerts", params={"festival_id": f["id"]}).json() == schedule


def test_create_concert_conflict_returns_409(client, base):
    f, s, _, _ = base
    other = post(client, "/artists", {"name": "Desert Crown", "genre": "Sludge"})
    r = client.post("/concerts", json={"festival_id": f["id"], "artist_id": other["id"], "stage_id": s["id"],
                                       "start_time": "2027-06-18T21:00:00", "end_time": "2027-06-18T22:00:00"})
    assert r.status_code == 409


def test_r5_missing_equipment_returns_400(client, base):
    f, s, _, _ = base
    picky = post(client, "/artists", {"name": "Iron Vow", "genre": "Heavy", "required_equipment": ["large_rigging"]})
    r = client.post("/concerts", json={"festival_id": f["id"], "artist_id": picky["id"], "stage_id": s["id"],
                                       "start_time": "2027-06-19T21:00:00", "end_time": "2027-06-19T22:00:00"})
    assert r.status_code == 400
    assert "large_rigging" in r.json()["detail"]


def test_r6_concert_outside_festival_returns_400(client, base):
    f, s, a, _ = base
    r = client.post("/concerts", json={"festival_id": f["id"], "artist_id": a["id"], "stage_id": s["id"],
                                       "start_time": "2027-06-25T21:00:00", "end_time": "2027-06-25T22:00:00"})
    assert r.status_code == 400


def test_unknown_references_return_404(client, base):
    f, s, a, _ = base
    r = client.post("/concerts", json={"festival_id": f["id"], "artist_id": 999, "stage_id": s["id"],
                                       "start_time": "2027-06-19T21:00:00", "end_time": "2027-06-19T22:00:00"})
    assert r.status_code == 404
    assert client.get("/concerts/999").status_code == 404
    assert client.patch("/concerts/999/reschedule", json={"start_time": "2027-06-19T21:00:00",
                                                          "end_time": "2027-06-19T22:00:00"}).status_code == 404
    assert client.post("/stages", json={"festival_id": 999, "name": "Temple", "capacity": 10}).status_code == 404


def test_duplicate_artist_returns_409(client, base):
    assert client.post("/artists", json={"name": "Solar Funeral", "genre": "Doom"}).status_code == 409


def test_reschedule_response_reports_notification(client, base):
    _, _, _, c = base
    r = client.patch(f"/concerts/{c['id']}/reschedule",
                     json={"start_time": "2027-06-18T22:00:00", "end_time": "2027-06-18T23:00:00"})
    assert r.status_code == 200
    assert r.json()["notification_status"] == "sent"


def test_publish_twice_returns_409(client, base):
    f = base[0]
    r = client.post(f"/festivals/{f['id']}/publish")
    assert r.status_code == 200 and r.json()["status"] == "published"
    assert client.post(f"/festivals/{f['id']}/publish").status_code == 409


def test_published_reschedule_requires_reason(client, base):
    f, _, _, c = base
    client.post(f"/festivals/{f['id']}/publish")
    r = client.post(f"/concerts/{c['id']}/published-reschedule",
                    json={"start_time": "2027-06-18T22:00:00", "end_time": "2027-06-18T23:00:00"})
    assert r.status_code == 422


def test_cancel_refused_once_published(client, base):
    f, _, _, c = base
    client.post(f"/festivals/{f['id']}/publish")
    assert client.post(f"/concerts/{c['id']}/cancel").status_code == 409


def test_r10_incidents(client, base):
    c = base[3]
    assert client.post("/incidents", json={"concert_id": 999, "description": "Coupure son"}).status_code == 404
    assert client.post("/incidents", json={"concert_id": c["id"], "description": "   "}).status_code == 400
    incident = post(client, "/incidents", {"concert_id": c["id"], "description": "Coupure son"})
    assert incident["resolved"] is False
    assert [i["id"] for i in client.get("/incidents", params={"concert_id": c["id"]}).json()] == [incident["id"]]
