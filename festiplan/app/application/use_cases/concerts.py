from dataclasses import dataclass
from datetime import datetime

from app.application.errors import NotFound
from app.application.notifications import EventDispatcher, OperationResult
from app.application.ports import ArtistRepository, FestivalRepository, StageRepository
from app.domain.model import Artist, Concert, Festival, Stage
from app.domain.value_objects import TimeSlot


def _load_concert_context(festivals: FestivalRepository, stages: StageRepository,
                          artists: ArtistRepository, concert_id: int) -> tuple[Festival, Stage, Artist]:
    festival = festivals.find_by_concert(concert_id)
    if festival is None:
        raise NotFound("Concert introuvable")
    concert = festival.concert(concert_id)
    stage, artist = stages.get(concert.stage_id), artists.get(concert.artist_id)
    if stage is None or artist is None:
        raise NotFound("Scène ou artiste du concert introuvable")
    return festival, stage, artist


@dataclass(frozen=True)
class ScheduleConcertCommand:
    festival_id: int
    artist_id: int
    stage_id: int
    start: datetime
    end: datetime


class ScheduleConcert:
    """Programmer un concert (R4 : références existantes, puis règles de l'agrégat)."""

    def __init__(self, festivals: FestivalRepository, stages: StageRepository, artists: ArtistRepository):
        self._festivals, self._stages, self._artists = festivals, stages, artists

    def execute(self, cmd: ScheduleConcertCommand) -> Concert:
        slot = TimeSlot(cmd.start, cmd.end)
        festival = self._festivals.get(cmd.festival_id)
        artist = self._artists.get(cmd.artist_id)
        stage = self._stages.get(cmd.stage_id)
        if festival is None or artist is None or stage is None:
            raise NotFound("Festival, artiste ou scène introuvable")
        concert = festival.schedule_concert(artist, stage, slot)
        self._festivals.save(festival)
        return concert


@dataclass(frozen=True)
class RescheduleConcertCommand:
    concert_id: int
    start: datetime
    end: datetime


class RescheduleConcert:
    """Déplacer un concert d'un planning en préparation."""

    def __init__(self, festivals: FestivalRepository, stages: StageRepository,
                 artists: ArtistRepository, events: EventDispatcher):
        self._festivals, self._stages, self._artists, self._events = festivals, stages, artists, events

    def execute(self, cmd: RescheduleConcertCommand) -> OperationResult[Concert]:
        slot = TimeSlot(cmd.start, cmd.end)
        festival, stage, artist = _load_concert_context(self._festivals, self._stages, self._artists, cmd.concert_id)
        concert = festival.reschedule_concert(cmd.concert_id, slot, stage, artist)
        self._festivals.save(festival)  # la modification est validée ici
        status = self._events.dispatch(festival.pull_events())  # puis seulement les effets secondaires
        return OperationResult(concert, status)


@dataclass(frozen=True)
class ReschedulePublishedConcertCommand:
    concert_id: int
    start: datetime
    end: datetime
    reason: str


class ReschedulePublishedConcert:
    """Procédure explicite de modification d'un planning déjà publié (motif obligatoire, public notifié)."""

    def __init__(self, festivals: FestivalRepository, stages: StageRepository,
                 artists: ArtistRepository, events: EventDispatcher):
        self._festivals, self._stages, self._artists, self._events = festivals, stages, artists, events

    def execute(self, cmd: ReschedulePublishedConcertCommand) -> OperationResult[Concert]:
        slot = TimeSlot(cmd.start, cmd.end)
        festival, stage, artist = _load_concert_context(self._festivals, self._stages, self._artists, cmd.concert_id)
        concert = festival.reschedule_published_concert(cmd.concert_id, slot, cmd.reason, stage, artist)
        self._festivals.save(festival)
        status = self._events.dispatch(festival.pull_events())
        return OperationResult(concert, status)


class CancelConcert:
    def __init__(self, festivals: FestivalRepository):
        self._festivals = festivals

    def execute(self, concert_id: int) -> Concert:
        festival = self._festivals.find_by_concert(concert_id)
        if festival is None:
            raise NotFound("Concert introuvable")
        concert = festival.cancel_concert(concert_id)
        self._festivals.save(festival)
        return concert
