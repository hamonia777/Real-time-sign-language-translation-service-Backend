from typing import Optional, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, TEXT, Text
from main.domain.Search.entity.search_history import SearchHistory

# 가령: 26/04/19 수정내용: Kakao 로그인 초기 상태(전화번호 미입력) 대응 위해 phone_num, nickname 을 Optional 로 변경 (+ master의 max_length 제약조건 병합)
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 두 브랜치의 장점을 합침 (Optional + max_length)
    kakao_id: Optional[str] = Field(default=None, max_length=255)
    email: Optional[str] = Field(default=None, max_length=50)
    nickname: Optional[str] = Field(default=None, max_length=50)
    phone_num: Optional[str] = Field(default=None, max_length=20)
    profile_image_url: Optional[str] = Field(default=None, max_length=255)
    
    kakao_access_token: Optional[str] = Field(default=None, sa_column=Column(Text))
    kakao_refresh_token: Optional[str] = Field(default=None, sa_column=Column(Text))
    kakao_notification_enabled: bool = Field(default=False)
    complete_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    nickname_updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    survey_profile: Optional["UserSurveyProfile"] = Relationship(back_populates="user")
    study_logs: List["StudyLog"] = Relationship(back_populates="user")
    learning_baskets: List["LearningBasket"] = Relationship(back_populates="user")
    inquiries: List["Inquiry"] = Relationship(back_populates="user")
    progress: List["UserLessonProgress"] = Relationship(back_populates="user")
    search_histories: List["SearchHistory"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})