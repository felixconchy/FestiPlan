from sqlalchemy.orm import Session
from app.models import Artist
from app.repositories.artist_repository import ArtistRepository

class ArtistService:
    def __init__(self, db: Session):
        self.db=db; self.repo=ArtistRepository(db)
    
    def list_artists(self):
        return self.repo.list()
    
    def create_artist(self, payload):
        return self.repo.create(Artist(name=payload.name,genre=payload.genre,required_equipment=",".join(payload.required_equipment)))
