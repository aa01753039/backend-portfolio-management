from fastapi import APIRouter

from app.api.routes import portfolio

api_router = APIRouter()

api_router.include_router(portfolio.router, tags=["portfolio"])