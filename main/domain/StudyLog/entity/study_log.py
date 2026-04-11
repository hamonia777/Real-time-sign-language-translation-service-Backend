from typing import Optional, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, TEXT

class StudyLog(SQLModel, table=True):
    __tablename__ = "study_log"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    study_date: Optional[date] = Field(default=None)
    lesson_count: int = Field(default=0)

    # Relationships
    user: "User" = Relationship(back_populates="study_logs")