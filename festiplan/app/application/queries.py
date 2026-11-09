"""Lectures (consultations) : pas de règle métier, une seule classe suffit.

Elles passent quand même par la couche application pour que les contrôleurs
ne dépendent jamais directement de la persistance.
"""
from app.application.errors import NotFound
from app.application.ports import (ArtistRepository, FestivalRepository, IncidentRepository,
                                   StageRepository)
from app.domain.model import Artist, Concert, Festival, Incident, Stage


class Queries:
    def __init__(self, festivals: FestivalRepository, stages: StageRepository,
                 artists: ArtistRepository, incidents: IncidentRepository):
        self._festivals, self._stages, self._artists, self._incidents = festivals, stages, artists, incidents

    def festivals(self) -> list[Festival]:
        return self._festivals.list()

    def artists(self) -> list[Artist]:
        return self._artists.list()

    def stages(self, festival_id: int) -> list[Stage]:
        return self._stages.list_for_festival(festival_id)

    def incidents(self, concert_id: int | None = None) -> list[Incident]:
        return self._incidents.list(concert_id)

    def concert(self, concert_id: int) -> Concert:
        festival = self._festivals.find_by_concert(concert_id)
        if festival is None:
            raise NotFound("Concert introuvable")
        return festival.concert(concert_id)

    def schedule(self, festival_id: int) -> list[Concert]:
        """Planning : concerts actifs d'un festival dans l'ordre chronologique."""
        festival = self._festivals.get(festival_id)
        if festival is None:
            raise NotFound("Festival introuvable")
        return festival.active_concerts
