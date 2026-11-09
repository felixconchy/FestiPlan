"""Tests de l'adaptateur de persistance SQLAlchemy (SQLite temporaire)."""
from datetime import datetime

from app.adapters.persistence.sql_repositories import (SqlArtistRepository, SqlFestivalRepository,
                                                       SqlIncidentRepository, SqlStageRepository)
from app.domain.model import Artist, ConcertStatus, Festival, Incident, ScheduleStatus, Stage
from app.domain.value_objects import Equipment, FestivalPeriod, TimeSlot


def at(h):
    return datetime(2027, 6, 18, h)


def test_festival_aggregate_roundtrip(db_session):
    festivals, stages, artists = (SqlFestivalRepository(db_session), SqlStageRepository(db_session),
                                  SqlArtistRepository(db_session))
    festival = Festival(None, "Hellforge", "Clisson", FestivalPeriod(at(10), at(23)))
    festivals.save(festival)
    stage = stages.add(Stage(None, festival.id, "Mainstage", 1000, Equipment.of(["special_lighting"])))
    artist = artists.add(Artist(None, "Iron Vow", "Heavy", Equipment.of(["special_lighting"])))

    concert = festival.schedule_concert(artist, stage, TimeSlot(at(18), at(19)))
    festivals.save(festival)
    assert concert.id is not None

    loaded = festivals.find_by_concert(concert.id)
    assert loaded.id == festival.id
    assert loaded.concert(concert.id).slot == TimeSlot(at(18), at(19))
    assert stages.get(stage.id).equipment == Equipment.of(["special_lighting"])
    assert artists.get_by_name("Iron Vow").required_equipment == Equipment.of(["special_lighting"])

    loaded.cancel_concert(concert.id)
    loaded.publish({}, {})
    festivals.save(loaded)
    reloaded = festivals.get(festival.id)
    assert reloaded.status == ScheduleStatus.PUBLISHED
    assert reloaded.concert(concert.id).status == ConcertStatus.CANCELLED


def test_incident_repository(db_session):
    festivals, stages, artists = (SqlFestivalRepository(db_session), SqlStageRepository(db_session),
                                  SqlArtistRepository(db_session))
    festival = Festival(None, "Hellforge", "Clisson", FestivalPeriod(at(10), at(23)))
    festivals.save(festival)
    stage = stages.add(Stage(None, festival.id, "Valley", 100))
    artist = artists.add(Artist(None, "Solar Funeral", "Doom"))
    concert = festival.schedule_concert(artist, stage, TimeSlot(at(18), at(19)))
    festivals.save(festival)

    incidents = SqlIncidentRepository(db_session)
    incidents.add(Incident(None, concert.id, "Coupure son", at(18)))
    incidents.add(Incident(None, concert.id, "Pluie", at(19)))
    assert [i.description for i in incidents.list(concert.id)] == ["Pluie", "Coupure son"]
    assert incidents.list(9999) == []
