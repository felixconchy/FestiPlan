from sqlalchemy.orm import Session
from app.models import Festival
from app.services.notification_service import NotificationService

class PublicationService:
    def __init__(self, db: Session): self.db=db; self.notifications=NotificationService()

    def publish(self, festival_id):
        festival=self.db.query(Festival).filter(Festival.id==festival_id).first()
        if festival is None: 
            return None
        # Contrôle métier incomplet intentionnel : conflits et contraintes non vérifiés avant publication.
        festival.status="published"; self.db.commit(); self.db.refresh(festival)
        self.notifications.notify_schedule_change(festival_id,f"Le planning du festival {festival.name} a été publié.")
        return festival
