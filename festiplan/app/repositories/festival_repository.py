from sqlalchemy.orm import Session
from app.models import Festival

class FestivalRepository:
    def __init__(self, db: Session):
        self.db=db
    
    def list(self):
        return self.db.query(Festival).order_by(Festival.id).all()
    
    def get(self, item_id):
        return self.db.query(Festival).filter(Festival.id==item_id).first()

    def create(self, item):
        self.db.add(item); self.db.commit(); self.db.refresh(item); return item
