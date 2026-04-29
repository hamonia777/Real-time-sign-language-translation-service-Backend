from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# 26.4.30 : 가령 : 수정 내용 - 학습 바구니 추가 요청 DTO 신규 추가
class LearningBasketAddRequestDto(BaseModel):
    lesson_id: int
    source: Optional[str] = None


# 26.4.30 : 가령 : 수정 내용 - 마이페이지 학습 바구니 조회 응답 항목 DTO 신규 추가
class LearningBasketItemDto(BaseModel):
    basket_id: int
    lesson_id: int
    title: str
    category: str
    subcategory: Optional[str] = None
    level: int
    video_url: str
    thumbnail_url: Optional[str] = None
    source: Optional[str] = None
    is_completed: bool = False
    created_at: datetime


# 26.4.30 : 가령 : 수정 내용 - 학습 바구니 목록 응답 DTO 신규 추가
class LearningBasketListResponseDto(BaseModel):
    total_count: int
    sort: str = "created_at_asc"
    items: List[LearningBasketItemDto]
    next_cursor: Optional[int] = None
    has_more: bool = False


# 26.4.30 : 가령 : 수정 내용 - 학습 바구니 추가/삭제 결과 응답 DTO 신규 추가
class LearningBasketMutationResponseDto(BaseModel):
    basket_id: int
    lesson_id: int
    user_id: int
    source: str
    created_at: datetime
    is_in_basket: bool
    message: str
