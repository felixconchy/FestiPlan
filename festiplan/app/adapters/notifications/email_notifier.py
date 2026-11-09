"""Adaptateur de notification : simule l'envoi d'un e-mail (aucun envoi réel)."""
import logging

from app.application.ports import NotificationError, Notifier
from app.domain.events import (ConcertRescheduled, DomainEvent, PublishedConcertRescheduled,
                               SchedulePublished)

logger = logging.getLogger(__name__)

PRODUCTION = "production@festiplan.test"
PUBLIC = "public@festiplan.test"


class EmailNotifier(Notifier):
    def __init__(self, fail: bool = False):
        self._fail = fail  # simulation d'une panne (FESTIPLAN_FAIL_NOTIFICATIONS)

    def notify(self, event: DomainEvent) -> None:
        recipient, subject, body = self._format(event)
        if self._fail:
            raise NotificationError("Simulation : le service de notification est indisponible")
        print(f"[FAKE EMAIL] to={recipient} subject={subject} body={body}")

    @staticmethod
    def _format(event: DomainEvent) -> tuple[str, str, str]:
        if isinstance(event, ConcertRescheduled):
            return PRODUCTION, f"Modification du concert #{event.concert_id}", \
                f"Concert déplacé au {event.start.isoformat()}"
        if isinstance(event, PublishedConcertRescheduled):
            return PUBLIC, f"Changement de programme : concert #{event.concert_id}", \
                f"Concert déplacé au {event.start.isoformat()} — motif : {event.reason}"
        if isinstance(event, SchedulePublished):
            return PUBLIC, f"Planning publié : {event.festival_name}", \
                f"Le planning du festival {event.festival_name} a été publié."
        return PRODUCTION, type(event).__name__, repr(event)
