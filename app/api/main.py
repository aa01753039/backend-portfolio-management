from fastapi import APIRouter

from app.api.routes import vacantes

api_router = APIRouter()
# api_router.include_router(login.router, tags=["login"])
api_router.include_router(vacantes.router, prefix="/vacantes", tags=["vacantes"])