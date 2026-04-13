from typing import Optional, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, TEXT

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    kakao_id: Optional[str] = Field(default=None, max_length=255)
    profile_image_url: Optional[str] = Field(default=None, max_length=255)
    nickname: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=50)
    phone_num: Optional[str] = Field(default=None, max_length=20)
    complete_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    survey_profile: Optional["UserSurveyProfile"] = Relationship(back_populates="user")
    study_logs: List["StudyLog"] = Relationship(back_populates="user")
    learning_baskets: List["LearningBasket"] = Relationship(back_populates="user")
    inquiries: List["Inquiry"] = Relationship(back_populates="user")
    progress: List["UserLessonProgress"] = Relationship(back_populates="user")