from fastapi import APIRouter, Depends

from app.adapters.http.dependencies import get_container
from app.adapters.http.schemas import StageCreate, StageRead
from app.application.use_cases.catalog import CreateStageCommand
from app.bootstrap import Container

router = APIRouter(prefix="/stages", tags=["stages"])


def stage_out(s):
    return {"id": s.id, "festival_id": s.festival_id, "name": s.name, "capacity": s.capacity,
            "available_equipment": s.equipment.as_list()}


@router.get("", response_model=list[StageRead])
def list_stages(festival_id: int, container: Container = Depends(get_container)):
    return [stage_out(s) for s in container.queries.stages(festival_id)]


@router.post("", response_model=StageRead, status_code=201)
def create_stage(payload: StageCreate, container: Container = Depends(get_container)):
    stage = container.create_stage.execute(
        CreateStageCommand(payload.festival_id, payload.name, payload.capacity, payload.available_equipment))
    return stage_out(stage)
