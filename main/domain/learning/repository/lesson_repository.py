from abc import ABC, abstractmethod
from typing import List, Optional

from fastapi import Depends
from sqlmodel import Session, select

from main.core.database import get_db
from main.domain.learning.entity.lesson import Lesson


class LessonRepository(ABC):
    @abstractmethod
    def find_by_id(self, lesson_id: int) -> Optional[Lesson]:
        pass

    @abstractmethod
    def find_by_category(self, category: str) -> List[Lesson]:
        pass

    @abstractmethod
    def find_by_title_and_category(self, title: str, category: str) -> Optional[Lesson]:
        pass

    @abstractmethod
    def save(self, lesson: Lesson) -> Lesson:
        pass


class SqlLessonRepository(LessonRepository):
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, lesson_id: int) -> Optional[Lesson]:
        return self.db.get(Lesson, lesson_id)

    def find_by_category(self, category: str) -> List[Lesson]:
        statement = select(Lesson).where(Lesson.category == category).order_by(Lesson.id)
        return list(self.db.execute(statement).scalars().all())

    def find_by_title_and_category(self, title: str, category: str) -> Optional[Lesson]:
        statement = (
            select(Lesson)
            .where(Lesson.title == title)
            .where(Lesson.category == category)
        )
        return self.db.execute(statement).scalars().first()

    def save(self, lesson: Lesson) -> Lesson:
        self.db.add(lesson)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson


def get_lesson_repository(db: Session = Depends(get_db)) -> LessonRepository:
    return SqlLessonRepository(db)
