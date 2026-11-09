from dataclasses import dataclass
from datetime import datetime, timezone

from app.application.errors import NotFound
from app.application.ports import FestivalRepository, IncidentRepository
from app.domain.model import Incident


@dataclass(frozen=True)
class ReportIncidentCommand:
    concert_id: int
    description: str
    occurred_at: datetime | None = None


class ReportIncident:
    """R10 : l'incident référence un concert existant (vérifié ici) et a une description (entité)."""

    def __init__(self, incidents: IncidentRepository, festivals: FestivalRepository):
        self._incidents, self._festivals = incidents, festivals

    def execute(self, cmd: ReportIncidentCommand) -> Incident:
        occurred_at = cmd.occurred_at or datetime.now(timezone.utc).replace(tzinfo=None)
        incident = Incident(None, cmd.concert_id, cmd.description, occurred_at)
        if self._festivals.find_by_concert(cmd.concert_id) is None:
            raise NotFound("Concert introuvable")
        return self._incidents.add(incident)


class ListIncidents:
    def __init__(self, incidents: IncidentRepository):
        self._incidents = incidents

    def execute(self, concert_id: int | None = None) -> list[Incident]:
        return self._incidents.list(concert_id)
