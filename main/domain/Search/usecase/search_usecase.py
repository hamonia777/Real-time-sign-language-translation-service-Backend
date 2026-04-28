from fastapi import Depends
from main.domain.Search.repository.search_repository import SearchRepository, get_search_repository
from main.domain.Search.dto.search_dto import (
    SearchResponseDto, SearchResultItem, 
    PopularSearchResponseDto, PopularSearchItem,
    RecentSearchResponseDto, RecentSearchItem
)

class SearchUseCase:
    def __init__(self, search_repo: SearchRepository = Depends(get_search_repository)):
        self.search_repo = search_repo

    async def search_word(self, user_id: int, word: str) -> SearchResponseDto:
        word = word.strip()
        if not word:
            return SearchResponseDto(keyword="", totalCount=0, results=[])

        lessons_data = await self.search_repo.find_lessons_by_word(user_id, word)
        
        if lessons_data:
            await self.search_repo.save_history(user_id, word)
        
        results = [
            SearchResultItem(
                id=lesson.id,
                word=lesson.title,
                isInBasket=is_in_basket,
                videoUrl=lesson.video_url if lesson.video_url else None
            ) for lesson, is_in_basket in lessons_data
        ]
        
        return SearchResponseDto(
            keyword=word,
            totalCount=len(results),
            results=results
        )

    async def get_popular(self) -> PopularSearchResponseDto:
        popular_data = await self.search_repo.get_popular_searches()
        
        results = [
            PopularSearchItem(rank=index + 1, word=word)
            for index, (word, count) in enumerate(popular_data)
        ]
        return PopularSearchResponseDto(popularSearches=results)

    async def get_recent(self, user_id: int) -> RecentSearchResponseDto:
        recent_data = await self.search_repo.get_recent_searches(user_id, limit=12)
        
        results = [
            RecentSearchItem(
                id=history.id,
                word=history.word,
                searchedAt=history.searched_at
            ) for history in recent_data
        ]
        return RecentSearchResponseDto(recentSearches=results)
    
    #26.04.28 혜미 추가 -> 단어 목록 반환용
    async def suggest_word(self, word: str) -> SearchResponseDto:
        """save_history 없이 단어 목록만 반환 (자동완성용)"""
        word = word.strip()
        if not word:
            return SearchResponseDto(keyword="", totalCount=0, results=[])

        lessons_data = await self.search_repo.find_lessons_by_word(0, word)
        results = [
            SearchResultItem(
                id=lesson.id,
                word=lesson.title,
                isInBasket=is_in_basket,
                videoUrl=lesson.video_url if lesson.video_url else None
            ) for lesson, is_in_basket in lessons_data
        ]
        return SearchResponseDto(keyword=word, totalCount=len(results), results=results)

    async def get_all_words(self) -> SearchResponseDto:
            """전체 단어 목록 반환 (가나다순)"""
            lessons_data = await self.search_repo.find_lessons_by_word(0, "")
            results = [
                SearchResultItem(
                    id=lesson.id,
                    word=lesson.title,
                    isInBasket=is_in_basket,
                    videoUrl=lesson.video_url if lesson.video_url else None
                ) for lesson, is_in_basket in lessons_data
            ]
            return SearchResponseDto(keyword="", totalCount=len(results), results=results)
    
    #26.04.28 혜미 추가 -> 최근 검색어 삭제용
    async def delete_recent(self, user_id: int, history_id: int):
        await self.search_repo.delete_history(user_id, history_id)
        return {"message": "삭제 완료"}