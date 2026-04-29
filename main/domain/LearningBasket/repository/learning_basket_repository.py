from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from fastapi import Depends
from sqlmodel import Session, select

from main.core.database import get_db
from main.domain.LearningBasket.entity.learning_basket import LearningBasket
from main.domain.UserLessonProgress.entity.user_lesson_progress import UserLessonProgress
from main.domain.learning.entity.lesson import Lesson


# 26.4.30 : 가령 : 수정 내용 - 학습 바구니 DB 접근용 Repository 신규 추가
class LearningBasketRepository(ABC):
    @abstractmethod
    def find_by_user_and_lesson(
        self, user_id: int, lesson_id: int
    ) -> Optional[LearningBasket]:
        pass

    @abstractmethod
    def find_by_id_and_user(
        self, basket_id: int, user_id: int
    ) -> Optional[LearningBasket]:
        pass

    @abstractmethod
    def find_by_user_with_lessons(
        self, user_id: int
    ) -> List[Tuple[LearningBasket, Lesson, Optional[UserLessonProgress]]]:
        pass

    @abstractmethod
    def save(self, basket: LearningBasket) -> LearningBasket:
        pass

    @abstractmethod
    def delete(self, basket: LearningBasket) -> None:
        pass


class SqlLearningBasketRepository(LearningBasketRepository):
    def __init__(self, db: Session):
        self.db = db

    def find_by_user_and_lesson(
        self, user_id: int, lesson_id: int
    ) -> Optional[LearningBasket]:
        statement = select(LearningBasket).where(
            LearningBasket.user_id == user_id,
            LearningBasket.lesson_id == lesson_id,
        )
        return self.db.execute(statement).scalars().first()

    def find_by_id_and_user(
        self, basket_id: int, user_id: int
    ) -> Optional[LearningBasket]:
        statement = select(LearningBasket).where(
            LearningBasket.id == basket_id,
            LearningBasket.user_id == user_id,
        )
        return self.db.execute(statement).scalars().first()

    def find_by_user_with_lessons(
        self, user_id: int
    ) -> List[Tuple[LearningBasket, Lesson, Optional[UserLessonProgress]]]:
        # 26.4.30 : 가령 : 수정 내용 - 바구니 항목과 lessons/progress를 조인해 category와 완료 여부 조회
        statement = (
            select(LearningBasket, Lesson, UserLessonProgress)
            .join(Lesson, LearningBasket.lesson_id == Lesson.id)
            .outerjoin(
                UserLessonProgress,
                (UserLessonProgress.lesson_id == LearningBasket.lesson_id)
                & (UserLessonProgress.user_id == LearningBasket.user_id),
            )
            .where(LearningBasket.user_id == user_id)
            .order_by(LearningBasket.created_at.asc())
        )
        return list(self.db.execute(statement).all())

    def save(self, basket: LearningBasket) -> LearningBasket:
        self.db.add(basket)
        self.db.commit()
        self.db.refresh(basket)
        return basket

    def delete(self, basket: LearningBasket) -> None:
        self.db.delete(basket)
        self.db.commit()


def get_learning_basket_repository(
    db: Session = Depends(get_db),
) -> LearningBasketRepository:
    return SqlLearningBasketRepository(db)
