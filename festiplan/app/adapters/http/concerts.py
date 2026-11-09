from fastapi import APIRouter, Depends

from app.adapters.http.dependencies import get_container
from app.adapters.http.schemas import (ConcertChangeRead, ConcertCreate, ConcertRead,
                                       ConcertReschedule, PublishedConcertReschedule)
from app.application.use_cases.concerts import (RescheduleConcertCommand,
                                                ReschedulePublishedConcertCommand,
                                                ScheduleConcertCommand)
from app.bootstrap import Container

router = APIRouter(prefix="/concerts", tags=["concerts"])


def concert_out(c, notification_status=None):
    data = {"id": c.id, "festival_id": c.festival_id, "artist_id": c.artist_id, "stage_id": c.stage_id,
            "start_time": c.slot.start, "end_time": c.slot.end, "status": c.status.value}
    if notification_status is not None:
        data["notification_status"] = notification_status.value
    return data


@router.get("", response_model=list[ConcertRead])
def list_concerts(festival_id: int, container: Container = Depends(get_container)):
    return [concert_out(c) for c in container.queries.schedule(festival_id)]


@router.get("/schedule/{festival_id}", response_model=list[ConcertRead])
def get_schedule(festival_id: int, container: Container = Depends(get_container)):
    return [concert_out(c) for c in container.queries.schedule(festival_id)]


@router.get("/{concert_id}", response_model=ConcertRead)
def get_concert(concert_id: int, container: Container = Depends(get_container)):
    return concert_out(container.queries.concert(concert_id))


@router.post("", response_model=ConcertRead, status_code=201)
def create_concert(payload: ConcertCreate, container: Container = Depends(get_container)):
    concert = container.schedule_concert.execute(ScheduleConcertCommand(
        payload.festival_id, payload.artist_id, payload.stage_id, payload.start_time, payload.end_time))
    return concert_out(concert)


@router.patch("/{concert_id}/reschedule", response_model=ConcertChangeRead)
def reschedule_concert(concert_id: int, payload: ConcertReschedule, container: Container = Depends(get_container)):
    """Déplacement ordinaire : refusé (409) si le planning est publié."""
    result = container.reschedule_concert.execute(
        RescheduleConcertCommand(concert_id, payload.start_time, payload.end_time))
    return concert_out(result.value, result.notification_status)


@router.post("/{concert_id}/published-reschedule", response_model=ConcertChangeRead)
def reschedule_published_concert(concert_id: int, payload: PublishedConcertReschedule,
                                 container: Container = Depends(get_container)):
    """Procédure explicite de modification d'un planning publié (motif obligatoire, public notifié)."""
    result = container.reschedule_published_concert.execute(
        ReschedulePublishedConcertCommand(concert_id, payload.start_time, payload.end_time, payload.reason))
    return concert_out(result.value, result.notification_status)


@router.post("/{concert_id}/cancel", response_model=ConcertRead)
def cancel_concert(concert_id: int, container: Container = Depends(get_container)):
    return concert_out(container.cancel_concert.execute(concert_id))
