from datetime import datetime

import pytest

from app.domain.model import Artist, Concert, Festival, Stage
from app.domain.value_objects import Equipment, FestivalPeriod, TimeSlot
from tests.fakes import (FakeNotifier, InMemoryArtistRepository, InMemoryFestivalRepository,
                         InMemoryIncidentRepository, InMemoryStageRepository)


def at(h, day=18):
    return datetime(2027, 6, day, h)


@pytest.fixture()
def repos():
    """Festival 1 : Iron Vow (concert 10, 18h-19h) et Crimson Engine (concert 11, 20h-21h) sur la Mainstage."""
    stages = InMemoryStageRepository(Stage(1, 1, "Mainstage", 50000, Equipment.of(["special_lighting"])),
                                     Stage(2, 1, "Warzone", 15000))
    artists = InMemoryArtistRepository(Artist(1, "Iron Vow", "Heavy"), Artist(2, "Crimson Engine", "Thrash"))
    festival = Festival(1, "Hellforge", "Clisson", FestivalPeriod(at(10), at(23, 20)), concerts=[
        Concert(10, 1, 1, 1, TimeSlot(at(18), at(19))),
        Concert(11, 1, 2, 1, TimeSlot(at(20), at(21))),
    ])
    return {"festivals": InMemoryFestivalRepository(festival), "stages": stages, "artists": artists,
            "incidents": InMemoryIncidentRepository(), "notifier": FakeNotifier()}
