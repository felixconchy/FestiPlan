"""Traduction des erreurs métier/applicatives en réponses HTTP (détail technique de l'adaptateur)."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.errors import AlreadyExists, NotFound
from app.domain.errors import (DomainError, InvalidTransition, ScheduleLocked,
                               SchedulingConflict)

_STATUS = [
    (NotFound, 404),
    (AlreadyExists, 409),
    (SchedulingConflict, 409),
    (ScheduleLocked, 409),
    (InvalidTransition, 409),
    (DomainError, 400),  # InvalidValue, RuleViolation
]


def register_error_handlers(app: FastAPI) -> None:
    async def handle(_: Request, exc: Exception):
        code = next(status for cls, status in _STATUS if isinstance(exc, cls))
        return JSONResponse(status_code=code, content={"detail": str(exc)})

    for cls, _ in _STATUS:
        app.add_exception_handler(cls, handle)
