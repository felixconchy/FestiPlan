from app.utils.email_sender import send_email

class NotificationService:
    def notify_schedule_change(self, concert_id, message):
        # Dépendance technique directe intentionnelle.
        send_email("production@festiplan.test",f"Modification du concert #{concert_id}",message)
