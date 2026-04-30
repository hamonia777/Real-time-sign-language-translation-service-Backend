from typing import Optional, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, TEXT

class LearningBasket(SQLModel, table=True):
    __tablename__ = "learning_baskets"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    lesson_id: int = Field(foreign_key="lessons.id")
    # 26.4.30 : 가령 : 수정 내용 - ERD 기준 source 기본값을 learning으로 설정
    source: str = Field(default="learning", max_length=20)
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(back_populates="learning_baskets")
    lesson: "Lesson" = Relationship(back_populates="baskets")
