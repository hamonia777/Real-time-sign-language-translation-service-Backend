from typing import Optional, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, TEXT

class UserSurveyProfile(SQLModel, table=True):
    __tablename__ = "user_survey_profiles"
    
    user_id: int = Field(primary_key=True, foreign_key="users.id")
    level: Optional[int] = Field(default=None)
    type: Optional[str] = Field(default=None, max_length=20)
    difficulty: Optional[str] = Field(default=None, max_length=20)

    # Relationships
    user: "User" = Relationship(back_populates="survey_profile")