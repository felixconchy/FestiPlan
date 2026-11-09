from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import StageCreate,StageRead
from app.services.stage_service import StageService
router=APIRouter(prefix="/stages",tags=["stages"])
def out(s): 
    return {
        "id":s.id,
        "festival_id":s.festival_id,
        "name":s.name,
        "capacity":s.capacity,
        "available_equipment":[x for x in s.available_equipment.split(",") if x]
    }

@router.get("",response_model=list[StageRead])
def list_stages(festival_id:int,db:Session=Depends(get_db)): 
    return [out(s) for s in StageService(db).list_stages(festival_id)]

@router.post("",response_model=StageRead,status_code=201)
def create_stage(payload:StageCreate,db:Session=Depends(get_db)):
    try:
        return out(StageService(db).create_stage(payload))
    except ValueError as exc:
        raise HTTPException(status_code=400,detail=str(exc))
