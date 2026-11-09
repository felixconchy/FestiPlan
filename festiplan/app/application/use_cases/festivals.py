from dataclasses import dataclass
from datetime import datetime

from app.application.errors import NotFound
from app.application.notifications import EventDispatcher, OperationResult
from app.application.ports import ArtistRepository, FestivalRepository, StageRepository
from app.domain.model import Festival
from app.domain.value_objects import FestivalPeriod


@dataclass(frozen=True)
class CreateFestivalCommand:
    name: str
    location: str
    start: datetime
    end: datetime


class CreateFestival:
    def __init__(self, festivals: FestivalRepository):
        self._festivals = festivals

    def execute(self, cmd: CreateFestivalCommand) -> Festival:
        festival = Festival(None, cmd.name, cmd.location, FestivalPeriod(cmd.start, cmd.end))
        self._festivals.save(festival)
        return festival



@dataclass(frozen=True)
class PublishScheduleCommand:
    festival_id: int


class PublishSchedule:
    """Publier le planning d'un festival (R8 vérifiée par l'agrégat)."""

    def __init__(self, festivals: FestivalRepository, stages: StageRepository,
                 artists: ArtistRepository, events: EventDispatcher):
        self._festivals, self._stages, self._artists, self._events = festivals, stages, artists, events

    def execute(self, cmd: PublishScheduleCommand) -> OperationResult[Festival]:
        festival = self._festivals.get(cmd.festival_id)
        if festival is None:
            raise NotFound("Festival introuvable")
        stages = {s.id: s for s in self._stages.list_for_festival(festival.id)}
        artist_ids = {c.artist_id for c in festival.active_concerts}
        artists = {a.id: a for a in map(self._artists.get, artist_ids) if a is not None}
        festival.publish(stages, artists)
        self._festivals.save(festival)
        status = self._events.dispatch(festival.pull_events())
        return OperationResult(festival, status)
