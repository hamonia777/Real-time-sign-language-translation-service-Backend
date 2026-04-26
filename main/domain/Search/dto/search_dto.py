from pydantic import BaseModel
from typing import List
from datetime import datetime

class SearchResultItem(BaseModel):
    id: int
    word: str
    isInBasket: bool

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