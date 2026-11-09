"""Artistes et scènes : opérations simples (proches du CRUD), les invariants restent dans les entités."""
from dataclasses import dataclass, field

from app.application.errors import AlreadyExists, NotFound
from app.application.ports import ArtistRepository, FestivalRepository, StageRepository
from app.domain.model import Artist, Stage
from app.domain.value_objects import Equipment


@dataclass(frozen=True)
class RegisterArtistCommand:
    name: str
    genre: str
    required_equipment: list[str] = field(default_factory=list)


class RegisterArtist:
    def __init__(self, artists: ArtistRepository):
        self._artists = artists

    def execute(self, cmd: RegisterArtistCommand) -> Artist:
        if self._artists.get_by_name(cmd.name) is not None:
            raise AlreadyExists(f"L'artiste « {cmd.name} » existe déjà")
        return self._artists.add(Artist(None, cmd.name, cmd.genre, Equipment.of(cmd.required_equipment)))



@dataclass(frozen=True)
class CreateStageCommand:
    festival_id: int
    name: str
    capacity: int
    available_equipment: list[str] = field(default_factory=list)


class CreateStage:
    def __init__(self, stages: StageRepository, festivals: FestivalRepository):
        self._stages, self._festivals = stages, festivals

    def execute(self, cmd: CreateStageCommand) -> Stage:
        stage = Stage(None, cmd.festival_id, cmd.name, cmd.capacity, Equipment.of(cmd.available_equipment))  # R9
        if self._festivals.get(cmd.festival_id) is None:
            raise NotFound("Festival introuvable")
        return self._stages.add(stage)
