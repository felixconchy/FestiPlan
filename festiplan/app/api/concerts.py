from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Concert
from app.schemas import ConcertCreate,ConcertRead,ConcertReschedule
from app.services.scheduling_service import SchedulingService
from app.utils.date_helpers import overlaps

router=APIRouter(prefix="/concerts",tags=["concerts"])

@router.get("",response_model=list[ConcertRead])
def list_concerts(festival_id:int,db:Session=Depends(get_db)):
    return SchedulingService(db).list_concerts(festival_id)

@router.get("/{concert_id}",response_model=ConcertRead)
def get_concert(concert_id:int,db:Session=Depends(get_db)):
    # Accès direct à SQLAlchemy depuis le contrôleur : défaut architectural.
    c=db.query(Concert).filter(Concert.id==concert_id).first()
    if c is None:
        raise HTTPException(status_code=404,detail="Concert introuvable")
    return c

@router.post("",response_model=ConcertRead,status_code=201)
def create_concert(payload:ConcertCreate,db:Session=Depends(get_db)):
    try:
        return SchedulingService(db).create_concert(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400,detail=str(exc))

@router.patch("/{concert_id}/reschedule",response_model=ConcertRead)
def reschedule_concert(concert_id:int,payload:ConcertReschedule,db:Session=Depends(get_db)):
    # Accès direct à SQLAlchemy dans le contrôleur : défaut architectural intentionnel.
    concert=db.query(Concert).filter(Concert.id==concert_id).first()
    if concert is None:
        raise HTTPException(status_code=404,detail="Concert introuvable")
    if payload.end_time<=payload.start_time:
        raise HTTPException(status_code=400,detail="La date de fin doit être postérieure au début")
    try: 
        return SchedulingService(db).reschedule_concert(concert_id,payload)
    except ValueError as exc:
        raise HTTPException(status_code=400,detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500,detail=str(exc))

@router.post("/{concert_id}/cancel",response_model=ConcertRead)
def cancel_concert(concert_id:int,db:Session=Depends(get_db)):
    c=SchedulingService(db).cancel_concert(concert_id)
    if c is None:
        raise HTTPException(status_code=404,detail="Concert introuvable")
    return c

@router.get("/schedule/{festival_id}",response_model=list[ConcertRead])
def get_schedule(festival_id:int,db:Session=Depends(get_db)):
    return SchedulingService(db).get_schedule(festival_id)
