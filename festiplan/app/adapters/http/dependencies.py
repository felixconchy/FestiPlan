from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.persistence.database import get_db
from app.bootstrap import Container, build_container


def get_container(db: Session = Depends(get_db)) -> Container:
    """Une session SQL et un conteneur par requête HTTP."""
    return build_container(db)
