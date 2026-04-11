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
