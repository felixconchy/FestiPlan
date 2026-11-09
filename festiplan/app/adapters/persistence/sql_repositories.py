"""Implémentations SQLAlchemy des ports de persistance.

Seul endroit qui connaît à la fois les modèles ORM et les objets du domaine.
"""
from sqlalchemy.orm import Session

from app.adapters.persistence.orm import ArtistRow, ConcertRow, FestivalRow, IncidentRow, StageRow
from app.application import ports
from app.domain.model import (Artist, Concert, ConcertStatus, Festival, Incident,
                              ScheduleStatus, Stage)
from app.domain.value_objects import Equipment, FestivalPeriod, TimeSlot


def _equipment(text: str) -> Equipment:
    return Equipment.of(text.split(","))


def _concert_to_domain(row: ConcertRow) -> Concert:
    return Concert(row.id, row.festival_id, row.artist_id, row.stage_id,
                   TimeSlot(row.start_time, row.end_time), ConcertStatus(row.status))


def _festival_to_domain(row: FestivalRow) -> Festival:
    return Festival(row.id, row.name, row.location, FestivalPeriod(row.start_date, row.end_date),
                    ScheduleStatus(row.status), [_concert_to_domain(c) for c in row.concerts])


def _stage_to_domain(row: StageRow) -> Stage:
    return Stage(row.id, row.festival_id, row.name, row.capacity, _equipment(row.available_equipment))


def _artist_to_domain(row: ArtistRow) -> Artist:
    return Artist(row.id, row.name, row.genre, _equipment(row.required_equipment))


def _incident_to_domain(row: IncidentRow) -> Incident:
    return Incident(row.id, row.concert_id, row.description, row.occurred_at, row.resolved)


class _SqlRepository:
    def __init__(self, session: Session):
        self._session = session

    def _insert(self, row):
        try:
            self._session.add(row)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        return row.id


class SqlFestivalRepository(_SqlRepository, ports.FestivalRepository):
    def list(self):
        return [_festival_to_domain(r) for r in self._session.query(FestivalRow).order_by(FestivalRow.id)]

    def get(self, festival_id):
        row = self._session.get(FestivalRow, festival_id)
        return _festival_to_domain(row) if row else None

    def find_by_concert(self, concert_id):
        row = self._session.get(ConcertRow, concert_id)
        return self.get(row.festival_id) if row else None

    def save(self, festival):
        try:
            row = self._session.get(FestivalRow, festival.id) if festival.id else None
            if row is None:
                row = FestivalRow()
                self._session.add(row)
            row.name, row.location = festival.name, festival.location
            row.start_date, row.end_date = festival.period.start, festival.period.end
            row.status = festival.status.value
            self._session.flush()
            festival.id = row.id
            for concert in festival.concerts:
                crow = self._session.get(ConcertRow, concert.id) if concert.id else None
                if crow is None:
                    crow = ConcertRow()
                    self._session.add(crow)
                crow.festival_id, crow.artist_id, crow.stage_id = festival.id, concert.artist_id, concert.stage_id
                crow.start_time, crow.end_time = concert.slot.start, concert.slot.end
                crow.status = concert.status.value
                self._session.flush()
                concert.id, concert.festival_id = crow.id, festival.id
            self._session.commit()  # une seule transaction pour tout l'agrégat
        except Exception:
            self._session.rollback()
            raise


class SqlStageRepository(_SqlRepository, ports.StageRepository):
    def get(self, stage_id):
        row = self._session.get(StageRow, stage_id)
        return _stage_to_domain(row) if row else None

    def list_for_festival(self, festival_id):
        rows = self._session.query(StageRow).filter(StageRow.festival_id == festival_id).order_by(StageRow.id)
        return [_stage_to_domain(r) for r in rows]

    def add(self, stage):
        stage.id = self._insert(StageRow(festival_id=stage.festival_id, name=stage.name, capacity=stage.capacity,
                                         available_equipment=",".join(stage.equipment.as_list())))
        return stage


class SqlArtistRepository(_SqlRepository, ports.ArtistRepository):
    def get(self, artist_id):
        row = self._session.get(ArtistRow, artist_id)
        return _artist_to_domain(row) if row else None

    def get_by_name(self, name):
        row = self._session.query(ArtistRow).filter(ArtistRow.name == name).first()
        return _artist_to_domain(row) if row else None

    def list(self):
        return [_artist_to_domain(r) for r in self._session.query(ArtistRow).order_by(ArtistRow.name)]

    def add(self, artist):
        artist.id = self._insert(ArtistRow(name=artist.name, genre=artist.genre,
                                           required_equipment=",".join(artist.required_equipment.as_list())))
        return artist


class SqlIncidentRepository(_SqlRepository, ports.IncidentRepository):
    def add(self, incident):
        incident.id = self._insert(IncidentRow(concert_id=incident.concert_id, description=incident.description,
                                               occurred_at=incident.occurred_at, resolved=incident.resolved))
        return incident

    def list(self, concert_id=None):
        query = self._session.query(IncidentRow)
        if concert_id is not None:
            query = query.filter(IncidentRow.concert_id == concert_id)
        return [_incident_to_domain(r) for r in query.order_by(IncidentRow.occurred_at.desc())]
