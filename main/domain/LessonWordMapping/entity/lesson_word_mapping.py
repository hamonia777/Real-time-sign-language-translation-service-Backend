# 가령: 260422: 수정 내용 - learning 브랜치에 엔티티 파일 미커밋 상태였어서 master 이력에서 복원
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
