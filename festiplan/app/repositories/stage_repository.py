from sqlalchemy.orm import Session
from app.models import Stage

class StageRepository:
    def __init__(self, db: Session):
        self.db=db
    
    def list_for_festival(self, festival_id):
        return self.db.query(Stage).filter(Stage.festival_id==festival_id).order_by(Stage.id).all()
    
    def get(self, item_id):
        return self.db.query(Stage).filter(Stage.id==item_id).first()
    
    def create(self, item):
        self.db.add(item); self.db.commit(); self.db.refresh(item); return item
