from typing import Optional, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, TEXT

class Lesson(SQLModel, table=True):
    __tablename__ = "lessons"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    video_url: Optional[str] = Field(default=None, max_length=500)
    title: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, max_length=20)
    subcategory: Optional[str] = Field(default=None, max_length=50)
    level: Optional[int] = Field(default=None)
    search_count: int = Field(default=0)

    # Relationships
    baskets: List["LearningBasket"] = Relationship(back_populates="lesson")
    progress: List["UserLessonProgress"] = Relationship(back_populates="lesson")