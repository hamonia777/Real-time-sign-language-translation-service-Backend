from abc import ABC, abstractmethod
from sqlmodel import Session, select, func
from fastapi import Depends
from typing import List, Tuple

from main.core.database import get_db
from main.domain.Search.entity.search_history import SearchHistory
from main.domain.learning.entity.lesson import Lesson
from main.domain.LearningBasket.entity.learning_basket import LearningBasket

class SearchRepository(ABC):
    @abstractmethod
    async def save_history(self, user_id: int, word: str) -> None: pass
    @abstractmethod
    async def find_lessons_by_word(self, user_id: int, word: str) -> List[Tuple[Lesson, bool]]: pass
    @abstractmethod
    async def get_popular_searches(self, limit: int = 3) -> List[Tuple[str, int]]: pass
    @abstractmethod
    async def get_recent_searches(self, user_id: int, limit: int = 10) -> List[SearchHistory]: pass

class SqlSearchRepository(SearchRepository):
    def __init__(self, db: Session):
        self.db = db

    async def save_history(self, user_id: int, word: str) -> None:
        history = SearchHistory(user_id=user_id, word=word)
        self.db.add(history)
        self.db.commit()

    async def find_lessons_by_word(self, user_id: int, word: str) -> List[Tuple[Lesson, bool]]:
        statement = (
            select(Lesson, LearningBasket.id.isnot(None).label("is_in_basket"))
            .outerjoin(LearningBasket, (LearningBasket.lesson_id == Lesson.id) & (LearningBasket.user_id == user_id))
            .where(Lesson.title.like(f"%{word}%")) 
        )
        result = self.db.execute(statement)
        return result.all()

    async def get_popular_searches(self, limit: int = 3) -> List[Tuple[str, int]]:
        statement = (
            select(SearchHistory.word, func.count(SearchHistory.id).label("count"))
            .group_by(SearchHistory.word)
            .order_by(func.count(SearchHistory.id).desc())
            .limit(limit)
        )
        result = self.db.execute(statement)
        return result.all()

    async def get_recent_searches(self, user_id: int, limit: int = 12) -> List[SearchHistory]:
        statement = (
            select(SearchHistory)
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.searched_at.desc())
            .limit(limit)
        )
        result = self.db.execute(statement)
        return result.scalars().all()

def get_search_repository(db: Session = Depends(get_db)) -> SearchRepository:
    return SqlSearchRepository(db)