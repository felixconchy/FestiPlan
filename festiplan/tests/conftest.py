"""Fixtures partagées.

Les imports techniques (FastAPI, SQLAlchemy) sont faits à l'intérieur des fixtures :
les tests du domaine et des cas d'utilisation ne démarrent ni l'API ni SQLite.
"""
import os
import tempfile

import pytest

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["FESTIPLAN_DATABASE_URL"] = f"sqlite:///{_tmp.name}"


@pytest.fixture(scope="session")
def database():
    from app.adapters.persistence.database import Base, engine
    from app.adapters.persistence import orm  # noqa: F401
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    try:
        os.unlink(_tmp.name)
    except OSError:
        pass


@pytest.fixture()
def db_session(database):
    from app.adapters.persistence.database import Base, SessionLocal
    db = SessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    yield db
    db.close()


@pytest.fixture()
def client(db_session):
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c
