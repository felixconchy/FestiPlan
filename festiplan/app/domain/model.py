"""Entités et agrégat du domaine FestiPlan (aucune dépendance technique)."""
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum

from app.domain.errors import (InvalidTransition, InvalidValue, RuleViolation,
                               ScheduleLocked, SchedulingConflict)
from app.domain.events import (ConcertRescheduled, DomainEvent,
                               PublishedConcertRescheduled, SchedulePublished)
from app.domain.value_objects import Equipment, FestivalPeriod, TimeSlot


class ScheduleStatus(str, Enum):
    PREPARATION = "preparation"
    PUBLISHED = "published"


class ConcertStatus(str, Enum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"


@dataclass(eq=False)
class Artist:
    id: int | None
    name: str
    genre: str
    required_equipment: Equipment = Equipment()


@dataclass(eq=False)
class Stage:
    id: int | None
    festival_id: int
    name: str
    capacity: int
    equipment: Equipment = Equipment()

    def __post_init__(self):
        if self.capacity <= 0:  # R9
            raise InvalidValue("La capacité d'une scène doit être strictement positive")


@dataclass(eq=False)
class Incident:
    id: int | None
    concert_id: int
    description: str
    occurred_at: datetime
    resolved: bool = False

    def __post_init__(self):
        if not self.description or not self.description.strip():  # R10
            raise InvalidValue("La description d'un incident ne peut pas être vide")
        self.description = self.description.strip()


@dataclass(eq=False)
class Concert:
    """Entité interne à l'agrégat Festival : ne se modifie que via le Festival."""
    id: int | None
    festival_id: int
    artist_id: int
    stage_id: int
    slot: TimeSlot
    status: ConcertStatus = ConcertStatus.SCHEDULED

    @property
    def is_active(self) -> bool:
        return self.status == ConcertStatus.SCHEDULED


@dataclass(eq=False)
class Festival:
    """Racine de l'agrégat « planning » : le festival et ses concerts.

    Toute modification de la programmation passe par cette classe afin de garantir
    R2, R3, R4, R5, R6, R7 et R8.
    """
    id: int | None
    name: str
    location: str
    period: FestivalPeriod
    status: ScheduleStatus = ScheduleStatus.PREPARATION
    concerts: list[Concert] = field(default_factory=list)
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    # --- lecture -------------------------------------------------------------------------
    @property
    def is_published(self) -> bool:
        return self.status == ScheduleStatus.PUBLISHED

    @property
    def active_concerts(self) -> list[Concert]:
        return sorted((c for c in self.concerts if c.is_active), key=lambda c: c.slot.start)

    def concert(self, concert_id: int) -> Concert | None:
        return next((c for c in self.concerts if c.id == concert_id), None)

    def pull_events(self) -> list[DomainEvent]:
        events, self._events = self._events, []
        return events

    # --- opérations ordinaires (planning en préparation) ---------------------------------
    def schedule_concert(self, artist: Artist, stage: Stage, slot: TimeSlot) -> Concert:
        self._ensure_in_preparation()
        concert = Concert(None, self.id, artist.id, stage.id, slot)
        self._check(concert, stage, artist)
        self.concerts.append(concert)
        return concert

    def reschedule_concert(self, concert_id: int, slot: TimeSlot, stage: Stage, artist: Artist) -> Concert:
        self._ensure_in_preparation()
        concert = self._move(concert_id, slot, stage, artist)
        self._events.append(ConcertRescheduled(concert.id, self.id, slot.start, slot.end))
        return concert

    def cancel_concert(self, concert_id: int) -> Concert:
        self._ensure_in_preparation()
        concert = self._require(concert_id)
        if not concert.is_active:
            raise InvalidTransition("Le concert est déjà annulé")
        concert.status = ConcertStatus.CANCELLED
        return concert

    # --- publication -----------------------------------------------------------------------
    def publish(self, stages: dict[int, Stage], artists: dict[int, Artist]) -> None:
        """R8 : on ne publie que si tous les concerts respectent les règles de programmation."""
        if self.is_published:
            raise InvalidTransition("Le planning est déjà publié")
        for concert in self.active_concerts:
            stage, artist = stages.get(concert.stage_id), artists.get(concert.artist_id)
            if stage is None or artist is None:
                raise RuleViolation(f"Concert #{concert.id} : scène ou artiste introuvable")
            self._check(concert, stage, artist)
        self.status = ScheduleStatus.PUBLISHED
        self._events.append(SchedulePublished(self.id, self.name))

    # --- procédure explicite de modification d'un planning publié (R7) --------------------
    def reschedule_published_concert(self, concert_id: int, slot: TimeSlot, reason: str,
                                     stage: Stage, artist: Artist) -> Concert:
        if not self.is_published:
            raise InvalidTransition("Procédure réservée à un planning publié : utilisez le déplacement ordinaire")
        if not reason or not reason.strip():
            raise InvalidValue("Le motif de modification d'un planning publié est obligatoire")
        concert = self._move(concert_id, slot, stage, artist)
        self._events.append(PublishedConcertRescheduled(concert.id, self.id, slot.start, slot.end, reason.strip()))
        return concert

    # --- règles internes -------------------------------------------------------------------
    def _ensure_in_preparation(self) -> None:
        if self.is_published:  # R7
            raise ScheduleLocked("Le planning est publié : utilisez la procédure de modification d'un planning publié")

    def _require(self, concert_id: int) -> Concert:
        concert = self.concert(concert_id)
        if concert is None:
            raise RuleViolation(f"Le concert #{concert_id} n'appartient pas à ce festival")
        return concert

    def _move(self, concert_id: int, slot: TimeSlot, stage: Stage, artist: Artist) -> Concert:
        concert = self._require(concert_id)
        if not concert.is_active:
            raise InvalidTransition("Un concert annulé ne peut pas être déplacé")
        self._check(replace(concert, slot=slot), stage, artist)  # on valide avant de modifier
        concert.slot = slot
        return concert

    def _check(self, concert: Concert, stage: Stage, artist: Artist) -> None:
        if stage.festival_id != self.id:  # R4
            raise RuleViolation("La scène n'appartient pas à ce festival")
        if not self.period.contains(concert.slot):  # R6
            raise RuleViolation("Le concert doit se dérouler pendant le festival")
        missing = artist.required_equipment.missing_from(stage.equipment)  # R5
        if missing:
            raise RuleViolation(f"La scène ne dispose pas des équipements requis : {', '.join(sorted(missing))}")
        for other in self.active_concerts:
            if other is concert or (concert.id is not None and other.id == concert.id):
                continue
            if not other.slot.overlaps(concert.slot):
                continue
            if other.stage_id == concert.stage_id:  # R2
                raise SchedulingConflict(f"Conflit : la scène est déjà occupée par le concert #{other.id}")
            if other.artist_id == concert.artist_id:  # R3
                raise SchedulingConflict(f"Conflit : l'artiste joue déjà le concert #{other.id} sur ce créneau")
