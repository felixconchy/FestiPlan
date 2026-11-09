from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from app.domain.errors import InvalidValue


@dataclass(frozen=True)
class TimeSlot:
    """Créneau horaire d'un concert. R1 : la fin est strictement après le début."""
    start: datetime
    end: datetime

    def __post_init__(self):
        if self.end <= self.start:
            raise InvalidValue("La date de fin doit être postérieure à la date de début")

    def overlaps(self, other: "TimeSlot") -> bool:
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class FestivalPeriod(TimeSlot):
    """Période du festival. R6 : un créneau doit y être entièrement contenu."""

    def contains(self, slot: TimeSlot) -> bool:
        return self.start <= slot.start and slot.end <= self.end


@dataclass(frozen=True)
class Equipment:
    """Ensemble d'équipements techniques (besoins d'un artiste ou dotation d'une scène)."""
    items: frozenset[str] = frozenset()

    @classmethod
    def of(cls, names: Iterable[str]) -> "Equipment":
        return cls(frozenset(n.strip() for n in names if n and n.strip()))

    def missing_from(self, available: "Equipment") -> set[str]:
        return set(self.items - available.items)

    def as_list(self) -> list[str]:
        return sorted(self.items)
