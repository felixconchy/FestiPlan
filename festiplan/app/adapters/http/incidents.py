from fastapi import APIRouter, Depends

from app.adapters.http.dependencies import get_container
from app.adapters.http.schemas import IncidentCreate, IncidentRead
from app.application.use_cases.incidents import ReportIncidentCommand
from app.bootstrap import Container

router = APIRouter(prefix="/incidents", tags=["incidents"])


def incident_out(i):
    return {"id": i.id, "concert_id": i.concert_id, "description": i.description,
            "occurred_at": i.occurred_at, "resolved": i.resolved}


@router.post("", response_model=IncidentRead, status_code=201)
def create_incident(payload: IncidentCreate, container: Container = Depends(get_container)):
    incident = container.report_incident.execute(
        ReportIncidentCommand(payload.concert_id, payload.description, payload.occurred_at))
    return incident_out(incident)


@router.get("", response_model=list[IncidentRead])
def list_incidents(concert_id: int | None = None, container: Container = Depends(get_container)):
    return [incident_out(i) for i in container.queries.incidents(concert_id)]
