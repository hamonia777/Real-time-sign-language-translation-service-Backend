# 가령: 26/04/19 수정내용: 병합 후 삭제된 user_lesson_progress 엔티티 복원 (relationship 없는 단순 버전)
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class UserLessonProgress(SQLModel, table=True):
    __tablename__ = "user_lesson_progress"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    lesson_id: int = Field(foreign_key="lessons.id")
    status: Optional[str] = Field(default=None, max_length=20)
    attempt: int = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.now)
