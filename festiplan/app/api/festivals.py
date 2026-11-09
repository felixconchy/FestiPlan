from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import FestivalCreate, FestivalRead
from app.services.festival_service import FestivalService
from app.services.publication_service import PublicationService

router=APIRouter(prefix="/festivals",tags=["festivals"])

@router.get("",response_model=list[FestivalRead])
def list_festivals(db:Session=Depends(get_db)): 
    return FestivalService(db).list_festivals()

@router.post("",response_model=FestivalRead,status_code=201)
def create_festival(payload:FestivalCreate,db:Session=Depends(get_db)):
    try:
        return FestivalService(db).create_festival(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400,detail=str(exc))

@router.post("/{festival_id}/publish",response_model=FestivalRead)
def publish_festival(festival_id:int,db:Session=Depends(get_db)):
    try:
        festival=PublicationService(db).publish(festival_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500,detail=str(exc))
    if festival is None:
        raise HTTPException(status_code=404,detail="Festival introuvable")
    return festival
