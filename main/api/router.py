from fastapi import APIRouter
from main.api.user import user_routes

api_router = APIRouter()

api_router.include_router(
    user_routes.router, 
    prefix="/users",
    tags=["Users"]
)