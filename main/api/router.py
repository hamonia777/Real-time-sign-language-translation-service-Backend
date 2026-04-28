# 가령: 26/04/19 수정내용: 병합으로 /api/learning 으로 돌아간 라우터 prefix 를 /api/v1/... 형식으로 복구
from fastapi import APIRouter
from main.api.user import user_routes
from main.api.learning import learning_routes
from main.api.survey import survey_routes
from main.api.profile import profile_routes
#from main.api.inquiry import inquiry_routes
from main.api.search import search_routes

api_router = APIRouter()

api_router.include_router(
    user_routes.router,
    prefix="/api/v1/users",
    tags=["Users"],
)

# 카카오 로그인은 /api/v1/auth/... 경로에도 노출 (프론트/카카오 개발자콘솔 redirect URI 호환)
api_router.include_router(
    user_routes.router,
    prefix="/api/v1/auth",
    tags=["Auth"],
)

api_router.include_router(
    survey_routes.router,
    prefix="/api/v1/users",
    tags=["Surveys"],
)

api_router.include_router(
    learning_routes.router,
    prefix="/api/v1/learning",
    tags=["Learning"],
)

api_router.include_router(
    profile_routes.router,
    prefix="/api/v1/profile",
    tags=["Profile"],
)

#api_router.include_router(
#    inquiry_routes.router,
#    prefix="/api/v1/inquiry",
#    tags=["Inquiry"],
#)

api_router.include_router(
    search_routes.router,
    prefix="/api/v1/search",
    tags=["Search"],
)