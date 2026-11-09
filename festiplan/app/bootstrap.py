"""Racine de composition : crée les adaptateurs concrets et les injecte dans les cas d'utilisation.

C'est le seul module qui connaît à la fois les cas d'utilisation et les implémentations techniques.
"""
from sqlalchemy.orm import Session

from app.adapters.notifications.email_notifier import EmailNotifier
from app.adapters.persistence.sql_repositories import (SqlArtistRepository,
                                                       SqlFestivalRepository,
                                                       SqlIncidentRepository,
                                                       SqlStageRepository)
from app.application.notifications import EventDispatcher
from app.application.queries import Queries
from app.application.ports import Notifier
from app.application.use_cases import catalog, concerts, festivals, incidents
from app.config import settings


class Container:
    def __init__(self, session: Session, notifier: Notifier):
        festival_repo = SqlFestivalRepository(session)
        stage_repo = SqlStageRepository(session)
        artist_repo = SqlArtistRepository(session)
        incident_repo = SqlIncidentRepository(session)
        events = EventDispatcher(notifier)

        self.create_festival = festivals.CreateFestival(festival_repo)
        self.publish_schedule = festivals.PublishSchedule(festival_repo, stage_repo, artist_repo, events)

        self.register_artist = catalog.RegisterArtist(artist_repo)
        self.create_stage = catalog.CreateStage(stage_repo, festival_repo)

        self.schedule_concert = concerts.ScheduleConcert(festival_repo, stage_repo, artist_repo)
        self.reschedule_concert = concerts.RescheduleConcert(festival_repo, stage_repo, artist_repo, events)
        self.reschedule_published_concert = concerts.ReschedulePublishedConcert(
            festival_repo, stage_repo, artist_repo, events)
        self.cancel_concert = concerts.CancelConcert(festival_repo)

        self.report_incident = incidents.ReportIncident(incident_repo, festival_repo)

        self.queries = Queries(festival_repo, stage_repo, artist_repo, incident_repo)


def build_container(session: Session) -> Container:
    return Container(session, EmailNotifier(fail=settings.fail_notifications))
