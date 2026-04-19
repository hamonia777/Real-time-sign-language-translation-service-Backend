from typing import Optional, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, TEXT

class LessonWordMapping(SQLModel, table=True):
    __tablename__ = "lesson_word_mappings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    sentence_lesson_id: int = Field(foreign_key="lessons.id")
    word_lesson_id: int = Field(foreign_key="lessons.id")
    word_order: Optional[int] = Field(default=None)