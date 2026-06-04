from fastapi import Depends, HTTPException, status

from main.domain.LearningBasket.dto.learning_basket_dto import (
    LearningBasketItemDto,
    LearningBasketListResponseDto,
    LearningBasketMutationResponseDto,
)
from main.domain.LearningBasket.entity.learning_basket import LearningBasket
from main.domain.LearningBasket.repository.learning_basket_repository import (
    LearningBasketRepository,
    get_learning_basket_repository,
)
from main.domain.learning.service.lesson_service import LessonService


MAX_ATTEMPTS = 3


# 26.4.30 : 가령 : 수정 내용 - 바구니 조회 시 완료된 학습 여부 계산
def _is_completed(progress) -> bool:
    if progress is None:
        return False
    return progress.status in ("completed", "passed") or progress.attempt >= MAX_ATTEMPTS


# 26.4.30 : 가령 : 수정 내용 - 마이페이지 학습 바구니 목록 조회 UseCase 신규 추가
class ListLearningBasketUseCase:
    def __init__(
        self,
        basket_repo: LearningBasketRepository = Depends(
            get_learning_basket_repository
        ),
    ):
        self.basket_repo = basket_repo

    def execute(self, user_id: int) -> LearningBasketListResponseDto:
        rows = self.basket_repo.find_by_user_with_lessons(user_id)
        items = [
            LearningBasketItemDto(
                basket_id=basket.id,
                lesson_id=lesson.id,
                title=lesson.title,
                category=lesson.category,
                subcategory=lesson.subcategory,
                level=lesson.level,
                video_url=lesson.video_url,
                thumbnail_url=lesson.thumbnail_url,
                source=basket.source,
                is_completed=_is_completed(progress),
                created_at=basket.created_at,
            )
            for basket, lesson, progress in rows
        ]
        return LearningBasketListResponseDto(
            total_count=len(items),
            sort="created_at_asc",
            items=items,
            next_cursor=items[-1].basket_id if items else None,
            has_more=False,
        )


# 26.4.30 : 가령 : 수정 내용 - 검색/학습 화면에서 학습 바구니에 항목 추가하는 UseCase 신규 추가
class AddLearningBasketUseCase:
    def __init__(
        self,
        lesson_service: LessonService = Depends(),
        basket_repo: LearningBasketRepository = Depends(
            get_learning_basket_repository
        ),
    ):
        self.lesson_service = lesson_service
        self.basket_repo = basket_repo

    def execute(
        self, user_id: int, lesson_id: int, source: str | None = None
    ) -> LearningBasketMutationResponseDto:
        self.lesson_service.get_lesson(lesson_id)

        existing = self.basket_repo.find_by_user_and_lesson(user_id, lesson_id)
        if existing:
            # 26.4.30 : 가령 : 수정 내용 - 중복 담기 방지를 위해 409 CONFLICT 반환
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 학습 바구니에 담겨 있습니다.",
            )

        source = source if source in ("search", "learning") else "learning"
        basket = self.basket_repo.save(
            LearningBasket(user_id=user_id, lesson_id=lesson_id, source=source)
        )
        return LearningBasketMutationResponseDto(
            basket_id=basket.id,
            lesson_id=lesson_id,
            user_id=user_id,
            source=basket.source,
            created_at=basket.created_at,
            is_in_basket=True,
            message="학습 바구니에 추가했습니다.",
        )


# 26.4.30 : 가령 : 수정 내용 - 학습 바구니 항목 삭제 UseCase 신규 추가
class RemoveLearningBasketUseCase:
    def __init__(
        self,
        basket_repo: LearningBasketRepository = Depends(
            get_learning_basket_repository
        ),
    ):
        self.basket_repo = basket_repo

    def execute(self, user_id: int, basket_id: int) -> LearningBasketMutationResponseDto:
        basket = self.basket_repo.find_by_id_and_user(basket_id, user_id)
        if not basket:
            raise HTTPException(status_code=404, detail="바구니 항목을 찾을 수 없습니다.")

        lesson_id = basket.lesson_id
        self.basket_repo.delete(basket)
        return LearningBasketMutationResponseDto(
            basket_id=basket_id,
            lesson_id=lesson_id,
            user_id=user_id,
            source=basket.source,
            created_at=basket.created_at,
            is_in_basket=False,
            message="학습 바구니에서 삭제했습니다.",
        )
