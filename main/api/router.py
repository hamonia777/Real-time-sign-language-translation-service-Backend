from fastapi import APIRouter
from main.api.user import user_routes
from main.api.learning import learning_routes

api_router = APIRouter()

api_router.include_router(
    user_routes.router,
    prefix="/users",
    tags=["Users"]
)

api_router.include_router(
    learning_routes.router,
    prefix="/api/learning",
    tags=["Learning"]
)