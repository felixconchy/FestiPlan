from dataclasses import dataclass
from datetime import datetime


class DomainEvent:
    """Fait métier qui s'est produit."""


@dataclass(frozen=True)
class ConcertRescheduled(DomainEvent):
    concert_id: int
    festival_id: int
    start: datetime
    end: datetime


@dataclass(frozen=True)
class PublishedConcertRescheduled(DomainEvent):
    concert_id: int
    festival_id: int
    start: datetime
    end: datetime
    reason: str


@dataclass(frozen=True)
class SchedulePublished(DomainEvent):
    festival_id: int
    festival_name: str
