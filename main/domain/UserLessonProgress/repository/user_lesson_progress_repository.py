# 가령: 26/04/19 수정내용: 학습 결과를 user_lesson_progress 테이블에 저장/조회하는 repository 신규 추가
from abc import ABC, abstractmethod
from typing import Optional

from fastapi import Depends
from sqlmodel import Session, select

from main.core.database import get_db
from main.domain.UserLessonProgress.entity.user_lesson_progress import UserLessonProgress


class UserLessonProgressRepository(ABC):
    @abstractmethod
    def find_by_user_and_lesson(
        self, user_id: int, lesson_id: int
    ) -> Optional[UserLessonProgress]:
        pass

    @abstractmethod
    def save(self, progress: UserLessonProgress) -> UserLessonProgress:
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


def get_user_lesson_progress_repository(
    db: Session = Depends(get_db),
) -> UserLessonProgressRepository:
    return SqlUserLessonProgressRepository(db)
