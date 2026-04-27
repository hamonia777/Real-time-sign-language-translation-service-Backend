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
                isInBasket=is_in_basket
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