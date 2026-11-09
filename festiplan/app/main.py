from fastapi import FastAPI

from app.adapters.http import artists, concerts, festivals, incidents, stages
from app.adapters.http.errors import register_error_handlers
from app.adapters.persistence import orm  # noqa: F401  (enregistre les tables)
from app.adapters.persistence.database import Base, engine
from app.config import settings

Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, version="0.2.0", description="API de gestion d'un festival fictif")
register_error_handlers(app)

for router in (festivals.router, artists.router, stages.router, concerts.router, incidents.router):
    app.include_router(router)


@app.get("/")
def health():
    return {"message": "Bienvenue sur FestiPlan", "status": "ok"}
