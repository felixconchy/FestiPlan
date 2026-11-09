from datetime import datetime

import pytest

from app.application.errors import AlreadyExists, NotFound
from app.application.use_cases.catalog import (CreateStage, CreateStageCommand, RegisterArtist,
                                               RegisterArtistCommand)
from app.application.queries import Queries
from app.application.use_cases.concerts import (CancelConcert, ScheduleConcert,
                                                ScheduleConcertCommand)
from app.application.use_cases.festivals import CreateFestival, CreateFestivalCommand
from app.application.use_cases.incidents import ReportIncident, ReportIncidentCommand
from app.domain.errors import InvalidValue, RuleViolation, SchedulingConflict
from tests.application.conftest import at


def test_create_festival_checks_period(repos):
    festival = CreateFestival(repos["festivals"]).execute(CreateFestivalCommand("Fest", "Nantes", at(10), at(20)))
    assert repos["festivals"].get(festival.id).name == "Fest"
    with pytest.raises(InvalidValue):
        CreateFestival(repos["festivals"]).execute(CreateFestivalCommand("Fest", "Nantes", at(20), at(10)))


def test_schedule_concert(repos):
    uc = ScheduleConcert(repos["festivals"], repos["stages"], repos["artists"])
    concert = uc.execute(ScheduleConcertCommand(1, 2, 2, at(18, day=19), at(19, day=19)))
    assert concert.id is not None
    assert repos["festivals"].get(1).concert(concert.id) is not None


def test_schedule_concert_rules(repos):
    uc = ScheduleConcert(repos["festivals"], repos["stages"], repos["artists"])
    with pytest.raises(NotFound):
        uc.execute(ScheduleConcertCommand(1, 99, 1, at(12), at(13)))
    with pytest.raises(SchedulingConflict):  # R3 : Iron Vow joue déjà à 18h sur la Mainstage
        uc.execute(ScheduleConcertCommand(1, 1, 2, at(18), at(19)))
    with pytest.raises(RuleViolation):  # R6
        uc.execute(ScheduleConcertCommand(1, 1, 2, at(8), at(9)))
    assert repos["festivals"].saved == 0


def test_cancel_concert_removes_it_from_schedule(repos):
    CancelConcert(repos["festivals"]).execute(10)
    queries = Queries(repos["festivals"], repos["stages"], repos["artists"], repos["incidents"])
    assert [c.id for c in queries.schedule(1)] == [11]
    with pytest.raises(NotFound):
        queries.schedule(99)


def test_register_artist_refuses_duplicates(repos):
    uc = RegisterArtist(repos["artists"])
    artist = uc.execute(RegisterArtistCommand("Pale Kingdom", "Atmospheric", ["special_lighting"]))
    assert repos["artists"].get(artist.id).required_equipment.as_list() == ["special_lighting"]
    with pytest.raises(AlreadyExists):
        uc.execute(RegisterArtistCommand("Pale Kingdom", "Atmospheric"))


def test_create_stage(repos):
    uc = CreateStage(repos["stages"], repos["festivals"])
    assert uc.execute(CreateStageCommand(1, "Temple", 10000)).id is not None
    with pytest.raises(InvalidValue):  # R9, même sans passer par HTTP
        uc.execute(CreateStageCommand(1, "Temple", 0))
    with pytest.raises(NotFound):
        uc.execute(CreateStageCommand(99, "Temple", 10))


def test_report_incident(repos):
    uc = ReportIncident(repos["incidents"], repos["festivals"])
    incident = uc.execute(ReportIncidentCommand(10, "  Coupure son  ", datetime(2027, 6, 18, 18, 30)))
    assert incident.description == "Coupure son"
    assert repos["incidents"].list(10) == [incident]
    with pytest.raises(NotFound):
        uc.execute(ReportIncidentCommand(999, "Coupure son"))
    with pytest.raises(InvalidValue):
        uc.execute(ReportIncidentCommand(10, ""))
