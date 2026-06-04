import httpx
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends
from main.core.security import get_current_user_id
from main.domain.Search.usecase.search_usecase import SearchUseCase
from main.domain.Search.dto.search_dto import SearchResponseDto, PopularSearchResponseDto, RecentSearchResponseDto

router = APIRouter()

# 26.04.28 혜미 추가 -> 초기화면에 전체 단어 목록 보여주는 API (가나다순)
# 26.4.30 : 가령 : 수정 내용 - 로그인 사용자 기준 isInBasket 계산을 위해 user_id 전달
@router.get("/all", response_model=SearchResponseDto)
async def all_words(
    usecase: SearchUseCase = Depends(),
    user_id: int = Depends(get_current_user_id)
):
    return await usecase.get_all_words(user_id)

# 26.04.28 혜미 추가 -> 자동완성 전용 API (save_history 없이 단어만 반환)
# 26.4.30 : 가령 : 수정 내용 - 자동완성 결과도 로그인 사용자 기준 바구니 여부 반영
@router.get("/suggest", response_model=SearchResponseDto)
async def suggest_words(
    word: str,
    usecase: SearchUseCase = Depends(),
    user_id: int = Depends(get_current_user_id)
):
    return await usecase.suggest_word(user_id, word)

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

# 26.04.28 혜미 추가 -> 최근 검색어 삭제
@router.delete("/recent/{history_id}")
async def delete_recent_search(
    history_id: int,
    usecase: SearchUseCase = Depends(),
    user_id: int = Depends(get_current_user_id)
):
    return await usecase.delete_recent(user_id, history_id)

@router.get("", response_model=SearchResponseDto)
async def search_words(
    word: str,
    usecase: SearchUseCase = Depends(),
    user_id: int = Depends(get_current_user_id)
):
    return await usecase.search_word(user_id, word)
