from fastapi import APIRouter, Depends

from app.adapters.http.dependencies import get_container
from app.adapters.http.schemas import FestivalChangeRead, FestivalCreate, FestivalRead
from app.application.use_cases.festivals import CreateFestivalCommand, PublishScheduleCommand
from app.bootstrap import Container

router = APIRouter(prefix="/festivals", tags=["festivals"])


def festival_out(f, notification_status=None):
    data = {"id": f.id, "name": f.name, "location": f.location, "start_date": f.period.start,
            "end_date": f.period.end, "status": f.status.value}
    if notification_status is not None:
        data["notification_status"] = notification_status.value
    return data


@router.get("", response_model=list[FestivalRead])
def list_festivals(container: Container = Depends(get_container)):
    return [festival_out(f) for f in container.queries.festivals()]


@router.post("", response_model=FestivalRead, status_code=201)
def create_festival(payload: FestivalCreate, container: Container = Depends(get_container)):
    festival = container.create_festival.execute(
        CreateFestivalCommand(payload.name, payload.location, payload.start_date, payload.end_date))
    return festival_out(festival)


@router.post("/{festival_id}/publish", response_model=FestivalChangeRead)
def publish_festival(festival_id: int, container: Container = Depends(get_container)):
    result = container.publish_schedule.execute(PublishScheduleCommand(festival_id))
    return festival_out(result.value, result.notification_status)
