from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SearchResultItem(BaseModel):
    id: int
    word: str
    isInBasket: bool
    videoUrl: Optional[str] = None

class SearchResponseDto(BaseModel):
    keyword: str
    totalCount: int
    results: List[SearchResultItem]

class PopularSearchItem(BaseModel):
    rank: int
    word: str

class PopularSearchResponseDto(BaseModel):
    popularSearches: List[PopularSearchItem]

class RecentSearchItem(BaseModel):
    id: int
    word: str
    searchedAt: datetime

class RecentSearchResponseDto(BaseModel):
    recentSearches: List[RecentSearchItem]