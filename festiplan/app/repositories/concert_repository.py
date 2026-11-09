from sqlalchemy.orm import Session
from app.models import Concert

class ConcertRepository:
    def __init__(self, db: Session):
        self.db=db

    def get(self, item_id):
        return self.db.query(Concert).filter(Concert.id==item_id).first()

    def list_for_festival(self, festival_id):
        return self.db.query(Concert).filter(Concert.festival_id==festival_id, Concert.status!="cancelled").order_by(Concert.start_time).all()
    
    def create(self, item):
        self.db.add(item); self.db.commit(); self.db.refresh(item); return item
