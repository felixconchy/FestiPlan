from sqlalchemy.orm import Session
from app.models import Artist, Concert, Festival, Stage
from app.repositories.concert_repository import ConcertRepository
from app.services.notification_service import NotificationService
from app.utils.date_helpers import overlaps

class SchedulingService:
    def __init__(self, db: Session): 
        self.db=db; self.repo=ConcertRepository(db); self.notifications=NotificationService()

    def list_concerts(self, festival_id): 
        return self.repo.list_for_festival(festival_id)

    def _check_conflicts(self, festival_id, artist_id, stage_id, start_time, end_time, exclude_id=None):
        rows=self.db.query(Concert).filter(Concert.festival_id==festival_id,Concert.status!="cancelled").all()
        for c in rows:
            if exclude_id is not None and c.id==exclude_id: 
                continue
            if overlaps(start_time,end_time,c.start_time,c.end_time):
                if c.stage_id==stage_id: 
                    raise ValueError("Conflit : la scène est déjà occupée")
                if c.artist_id==artist_id: 
                    raise ValueError("Conflit : l'artiste est déjà programmé")

    def create_concert(self, payload):
        festival=self.db.query(Festival).filter(Festival.id==payload.festival_id).first()
        artist=self.db.query(Artist).filter(Artist.id==payload.artist_id).first()
        stage=self.db.query(Stage).filter(Stage.id==payload.stage_id).first()
        if festival is None or artist is None or stage is None:
            raise ValueError("Festival, artiste ou scène introuvable")
        if stage.festival_id != festival.id:
            raise ValueError("La scène n'appartient pas à ce festival")
        if payload.end_time <= payload.start_time:
            raise ValueError("La date de fin doit être postérieure à la date de début")
        if payload.start_time < festival.start_date or payload.end_time > festival.end_date: 
            raise ValueError("Le concert doit se dérouler pendant le festival")
        self._check_conflicts(payload.festival_id,payload.artist_id,payload.stage_id,payload.start_time,payload.end_time)
        required={x.strip() for x in artist.required_equipment.split(",") if x.strip()}
        available={x.strip() for x in stage.available_equipment.split(",") if x.strip()}
        if not required.issubset(available): 
            raise ValueError("La scène ne dispose pas de tous les équipements requis")
        return self.repo.create(Concert(festival_id=payload.festival_id,artist_id=payload.artist_id,stage_id=payload.stage_id,start_time=payload.start_time,end_time=payload.end_time))
    
    def reschedule_concert(self, concert_id, payload):
        concert=self.repo.get(concert_id)
        if concert is None:
            return None
        if payload.end_time <= payload.start_time: 
            raise ValueError("La date de fin doit être postérieure à la date de début")
        # DÉFAUT INTENTIONNEL 1 : les conflits, équipements, dates du festival et statut publié ne sont pas contrôlés ici.
        concert.start_time=payload.start_time; concert.end_time=payload.end_time
        self.db.commit(); self.db.refresh(concert)
        # DÉFAUT INTENTIONNEL 2 : notification après commit ; une panne produit une réponse 500 après persistance.
        self.notifications.notify_schedule_change(concert.id,f"Concert déplacé au {concert.start_time.isoformat()}")
        return concert
    
    def cancel_concert(self, concert_id):
        concert=self.repo.get(concert_id)
        if concert is None: 
            return None
        concert.status="cancelled"; self.db.commit(); self.db.refresh(concert); return concert
    
    def get_schedule(self, festival_id): 
        return self.list_concerts(festival_id)
