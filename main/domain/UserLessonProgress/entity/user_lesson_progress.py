from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class UserLessonProgress(SQLModel, table=True):
    __tablename__ = "user_lesson_progress"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    lesson_id: int = Field(foreign_key="lessons.id")
    status: Optional[str] = Field(default=None, max_length=20)
    attempt: int = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 문자열로 "User", "Lesson"을 넣어 순환 참조 방지
    user: Optional["User"] = Relationship(back_populates="progress")
    lesson: Optional["Lesson"] = Relationship(back_populates="progress")