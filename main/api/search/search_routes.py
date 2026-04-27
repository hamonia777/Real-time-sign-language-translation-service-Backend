from fastapi import APIRouter, Depends
from main.core.security import get_current_user_id
from main.domain.Search.usecase.search_usecase import SearchUseCase
from main.domain.Search.dto.search_dto import SearchResponseDto, PopularSearchResponseDto, RecentSearchResponseDto

router = APIRouter()

@router.get("", response_model=SearchResponseDto)
async def search_words(
    word: str,
    usecase: SearchUseCase = Depends(),
    user_id: int = Depends(get_current_user_id)
):
    return await usecase.search_word(user_id, word)

@router.get("/popular", response_model=PopularSearchResponseDto)
async def popular_searches(
    usecase: SearchUseCase = Depends(),
    user_id: int = Depends(get_current_user_id)
):
    return await usecase.get_popular()

@router.get("/recent", response_model=RecentSearchResponseDto)
async def recent_searches(
    usecase: SearchUseCase = Depends(),
    user_id: int = Depends(get_current_user_id)
):
    return await usecase.get_recent(user_id)