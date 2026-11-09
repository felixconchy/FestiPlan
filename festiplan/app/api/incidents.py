from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Incident,Concert
from app.schemas import IncidentCreate,IncidentRead

router=APIRouter(prefix="/incidents",tags=["incidents"])

@router.post("",response_model=IncidentRead,status_code=201)
def create_incident(payload:IncidentCreate,db:Session=Depends(get_db)):
    if db.query(Concert).filter(Concert.id==payload.concert_id).first() is None: 
        raise HTTPException(status_code=404,detail="Concert introuvable")
    row=Incident(concert_id=payload.concert_id,
                 description=payload.description,
                 occurred_at=payload.occurred_at)
    db.add(row); db.commit(); db.refresh(row); return row

@router.get("",response_model=list[IncidentRead])
def list_incidents(concert_id:int|None=None,db:Session=Depends(get_db)):
    q=db.query(Incident)
    if concert_id is not None:
        q=q.filter(Incident.concert_id==concert_id)
    return q.order_by(Incident.occurred_at.desc()).all()
