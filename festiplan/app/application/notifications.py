"""Transmission des événements de domaine au notificateur, APRÈS validation de la modification.

Décision (défaut 2) : la notification est un effet secondaire. Son échec est journalisé
et signalé dans le résultat, mais n'annule pas et ne masque pas l'opération métier.
"""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

from app.application.ports import Notifier
from app.domain.events import DomainEvent

logger = logging.getLogger(__name__)
T = TypeVar("T")


class NotificationStatus(str, Enum):
    SENT = "sent"
    FAILED = "failed"
    NONE = "none"


@dataclass(frozen=True)
class OperationResult(Generic[T]):
    value: T
    notification_status: NotificationStatus


class EventDispatcher:
    def __init__(self, notifier: Notifier):
        self._notifier = notifier

    def dispatch(self, events: list[DomainEvent]) -> NotificationStatus:
        if not events:
            return NotificationStatus.NONE
        status = NotificationStatus.SENT
        for event in events:
            try:
                self._notifier.notify(event)
            except Exception:  # un effet secondaire ne doit jamais faire échouer l'opération
                logger.exception("Échec de la notification pour %s", event)
                status = NotificationStatus.FAILED
        return status
