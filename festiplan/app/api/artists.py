from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ArtistCreate,ArtistRead
from app.services.artist_service import ArtistService

router=APIRouter(prefix="/artists",tags=["artists"])

def out(a):
    return {
        "id":a.id,
        "name":a.name,
        "genre":a.genre,
        "required_equipment":[x for x in a.required_equipment.split(",") if x]
        }

@router.get("",response_model=list[ArtistRead])
def list_artists(db:Session=Depends(get_db)):
    return [out(a) for a in ArtistService(db).list_artists()]

@router.post("",response_model=ArtistRead,status_code=201)
def create_artist(payload:ArtistCreate,db:Session=Depends(get_db)): return out(ArtistService(db).create_artist(payload))
