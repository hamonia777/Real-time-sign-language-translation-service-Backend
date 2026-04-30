# 가령: 26/04/19 수정내용: 학습 결과를 user_lesson_progress 테이블에 저장/조회하는 repository 신규 추가
from abc import ABC, abstractmethod
from datetime import date, datetime, time
from typing import List, Optional, Tuple

from fastapi import Depends
from sqlalchemy import func
from sqlmodel import Session, select

from main.core.database import get_db
from main.domain.UserLessonProgress.entity.user_lesson_progress import UserLessonProgress
from main.domain.learning.entity.lesson import Lesson


class UserLessonProgressRepository(ABC):
    @abstractmethod
    def find_by_user_and_lesson(
        self, user_id: int, lesson_id: int
    ) -> Optional[UserLessonProgress]:
        pass

    @abstractmethod
    def save(self, progress: UserLessonProgress) -> UserLessonProgress:
        pass

    @abstractmethod
    def find_by_user_with_lessons(
        self, user_id: int
    ) -> List[Tuple[UserLessonProgress, Lesson]]:
        pass

    @abstractmethod
    def count_by_user_grouped_by_date(
        self, user_id: int, start_date: date
    ) -> List[Tuple[date, int]]:
        pass


class SqlUserLessonProgressRepository(UserLessonProgressRepository):
    def __init__(self, db: Session):
        self.db = db

    def find_by_user_and_lesson(
        self, user_id: int, lesson_id: int
    ) -> Optional[UserLessonProgress]:
        statement = select(UserLessonProgress).where(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == lesson_id,
        )
        return self.db.execute(statement).scalars().first()

    def save(self, progress: UserLessonProgress) -> UserLessonProgress:
        self.db.add(progress)
        self.db.commit()
        self.db.refresh(progress)
        return progress

    def find_by_user_with_lessons(
        self, user_id: int
    ) -> List[Tuple[UserLessonProgress, Lesson]]:
        statement = (
            select(UserLessonProgress, Lesson)
            .join(Lesson, UserLessonProgress.lesson_id == Lesson.id)
            .where(UserLessonProgress.user_id == user_id)
            .order_by(UserLessonProgress.updated_at.desc())
        )
        return list(self.db.execute(statement).all())

    def count_by_user_grouped_by_date(
        self, user_id: int, start_date: date
    ) -> List[Tuple[date, int]]:
        start_at = datetime.combine(start_date, time.min)
        progress_date = func.date(UserLessonProgress.updated_at)
        statement = (
            select(progress_date, func.count(UserLessonProgress.id))
            .where(
                UserLessonProgress.user_id == user_id,
                UserLessonProgress.updated_at >= start_at,
            )
            .group_by(progress_date)
            .order_by(progress_date)
        )

        rows = self.db.execute(statement).all()
        result: List[Tuple[date, int]] = []
        for day_value, count in rows:
            if isinstance(day_value, str):
                day_value = date.fromisoformat(day_value)
            result.append((day_value, int(count)))
        return result


def get_user_lesson_progress_repository(
    db: Session = Depends(get_db),
) -> UserLessonProgressRepository:
    return SqlUserLessonProgressRepository(db)
