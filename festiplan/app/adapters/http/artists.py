from fastapi import APIRouter, Depends

from app.adapters.http.dependencies import get_container
from app.adapters.http.schemas import ArtistCreate, ArtistRead
from app.application.use_cases.catalog import RegisterArtistCommand
from app.bootstrap import Container

router = APIRouter(prefix="/artists", tags=["artists"])


def artist_out(a):
    return {"id": a.id, "name": a.name, "genre": a.genre, "required_equipment": a.required_equipment.as_list()}


@router.get("", response_model=list[ArtistRead])
def list_artists(container: Container = Depends(get_container)):
    return [artist_out(a) for a in container.list_artists.execute()]


@router.post("", response_model=ArtistRead, status_code=201)
def create_artist(payload: ArtistCreate, container: Container = Depends(get_container)):
    artist = container.register_artist.execute(
        RegisterArtistCommand(payload.name, payload.genre, payload.required_equipment))
    return artist_out(artist)
