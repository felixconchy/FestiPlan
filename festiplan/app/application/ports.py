"""Ports sortants : contrats dont le cœur applicatif a besoin.

Les implémentations (SQLAlchemy, e-mail...) sont dans app/adapters.
"""
from abc import ABC, abstractmethod

from app.domain.events import DomainEvent
from app.domain.model import Artist, Festival, Incident, Stage


class FestivalRepository(ABC):
    """Charge et sauvegarde l'agrégat Festival complet (festival + concerts)."""

    @abstractmethod
    def list(self) -> list[Festival]: ...

    @abstractmethod
    def get(self, festival_id: int) -> Festival | None: ...

    @abstractmethod
    def find_by_concert(self, concert_id: int) -> Festival | None: ...

    @abstractmethod
    def save(self, festival: Festival) -> None:
        """Persiste l'agrégat de façon atomique et attribue les identifiants manquants."""


class StageRepository(ABC):
    @abstractmethod
    def get(self, stage_id: int) -> Stage | None: ...

    @abstractmethod
    def list_for_festival(self, festival_id: int) -> list[Stage]: ...

    @abstractmethod
    def add(self, stage: Stage) -> Stage: ...


class ArtistRepository(ABC):
    @abstractmethod
    def get(self, artist_id: int) -> Artist | None: ...

    @abstractmethod
    def get_by_name(self, name: str) -> Artist | None: ...

    @abstractmethod
    def list(self) -> list[Artist]: ...

    @abstractmethod
    def add(self, artist: Artist) -> Artist: ...


class IncidentRepository(ABC):
    @abstractmethod
    def add(self, incident: Incident) -> Incident: ...

    @abstractmethod
    def list(self, concert_id: int | None = None) -> list[Incident]: ...


class NotificationError(Exception):
    """Échec technique d'envoi d'une notification."""


class Notifier(ABC):
    @abstractmethod
    def notify(self, event: DomainEvent) -> None:
        """Envoie une notification ; lève NotificationError en cas d'échec."""
