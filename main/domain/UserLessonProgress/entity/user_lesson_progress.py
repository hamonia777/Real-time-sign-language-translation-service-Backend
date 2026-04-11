from typing import Optional, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, TEXT

class UserLessonProgress(SQLModel, table=True):
    __tablename__ = "user_lesson_progress"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    lesson_id: int = Field(foreign_key="lessons.id")
    status: Optional[str] = Field(default=None, max_length=20)
    attempt: int = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(back_populates="progress")
    lesson: "Lesson" = Relationship(back_populates="progress")