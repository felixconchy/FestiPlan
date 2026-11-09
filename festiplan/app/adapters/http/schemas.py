"""Schémas Pydantic : validation du FORMAT des requêtes HTTP et forme des réponses.

Les règles métier ne sont pas ici : elles sont dans le domaine.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class FestivalCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=120)
    start_date: datetime
    end_date: datetime


class FestivalRead(FestivalCreate):
    id: int
    status: str


class FestivalChangeRead(FestivalRead):
    notification_status: str


class ArtistCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    genre: str = Field(min_length=2, max_length=80)
    required_equipment: list[str] = []


class ArtistRead(BaseModel):
    id: int
    name: str
    genre: str
    required_equipment: list[str]


class StageCreate(BaseModel):
    festival_id: int
    name: str = Field(min_length=2, max_length=100)
    capacity: int = Field(gt=0)
    available_equipment: list[str] = []


class StageRead(BaseModel):
    id: int
    festival_id: int
    name: str
    capacity: int
    available_equipment: list[str]


class ConcertCreate(BaseModel):
    festival_id: int
    artist_id: int
    stage_id: int
    start_time: datetime
    end_time: datetime


class ConcertReschedule(BaseModel):
    start_time: datetime
    end_time: datetime


class PublishedConcertReschedule(ConcertReschedule):
    reason: str = Field(min_length=3, max_length=500,
                        description="Motif obligatoire de la modification d'un planning publié")


class ConcertRead(BaseModel):
    id: int
    festival_id: int
    artist_id: int
    stage_id: int
    start_time: datetime
    end_time: datetime
    status: str


class ConcertChangeRead(ConcertRead):
    notification_status: str = Field(description="sent | failed | none : résultat de l'effet secondaire, "
                                                 "indépendant de la réussite de l'opération")


class IncidentCreate(BaseModel):
    concert_id: int
    description: str = Field(min_length=3, max_length=2000)
    occurred_at: datetime | None = None


class IncidentRead(BaseModel):
    id: int
    concert_id: int
    description: str
    occurred_at: datetime
    resolved: bool
