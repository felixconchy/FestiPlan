from sqlalchemy.orm import Session
from app.models import Festival, Stage
from app.repositories.stage_repository import StageRepository

class StageService:
    def __init__(self, db: Session): self.db=db; self.repo=StageRepository(db)

    def list_stages(self, festival_id): 
        return self.repo.list_for_festival(festival_id)

    def create_stage(self, payload):
        if self.db.query(Festival).filter(Festival.id==payload.festival_id).first() is None:
            raise ValueError("Festival introuvable")
        return self.repo.create(Stage(festival_id=payload.festival_id,name=payload.name,capacity=payload.capacity,available_equipment=",".join(payload.available_equipment)))
