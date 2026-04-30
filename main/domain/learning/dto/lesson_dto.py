from datetime import datetime
from datetime import date
from typing import List, Optional
from pydantic import BaseModel


class LessonResponseDto(BaseModel):
    lesson_id: int
    title: str
    category: str
    subcategory: Optional[str] = None
    level: int
    video_url: str
    thumbnail_url: Optional[str] = None


class LessonListResponseDto(BaseModel):
    total_count: int
    items: List[LessonResponseDto]


class SeedResponseDto(BaseModel):
    inserted: int
    skipped: int
    total: int
    message: str


# 가령: 260422: 수정 내용 - 문장 시드 응답 DTO. 매핑 카운트와 매칭 실패 단어 목록을 함께 반환
class SeedSentencesResponseDto(BaseModel):
    inserted_sentences: int
    skipped_sentences: int
    inserted_mappings: int
    deleted_mappings: int
    missing_words: List[str]
    total_lines: int
    message: str


# 가령: 260422: 수정 내용 - 문장 학습 페이지에서 문장+수어어순단어 한 번에 받기 위한 DTO
class SentenceWordItemDto(BaseModel):
    word_order: int
    lesson_id: int
    title: str


class SentenceWithWordsResponseDto(BaseModel):
    sentence_id: int
    sentence_title: str
    words: List[SentenceWordItemDto]


class SaveResultRequestDto(BaseModel):
    lesson_id: int
    score: float
    attempt: int = 1


class SaveResultResponseDto(BaseModel):
    lesson_id: int
    score: float
    is_passed: bool
    attempt: int
    pass_threshold: float = 80.0


class LessonProgressItemDto(BaseModel):
    lesson_id: int
    title: str
    category: str
    subcategory: Optional[str] = None
    level: int
    status: str
    attempt: int
    progress_percent: int
    updated_at: datetime


class MyLearningProgressResponseDto(BaseModel):
    completed_count: int
    in_progress_count: int
    completed: List[LessonProgressItemDto]
    in_progress: List[LessonProgressItemDto]


class LearningProgressListResponseDto(BaseModel):
    total_count: int
    items: List[LessonProgressItemDto]
    next_cursor: Optional[int] = None
    has_more: bool = False


class AchievementDayDto(BaseModel):
    date: date
    count: int


class AchievementResponseDto(BaseModel):
    start_date: date
    end_date: date
    days: List[AchievementDayDto]
