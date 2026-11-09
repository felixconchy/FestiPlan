from sqlalchemy.orm import Session
from app.models import Artist

class ArtistRepository:
    def __init__(self, db: Session):
        self.db=db
    
    def list(self):
        return self.db.query(Artist).order_by(Artist.name).all()
    
    def get(self, item_id):
        return self.db.query(Artist).filter(Artist.id==item_id).first()
    
    def create(self, item):
        self.db.add(item); self.db.commit(); self.db.refresh(item); return item
