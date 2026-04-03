from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

class UserSignUpDto(SQLModel):
    nickname: str
    phone_num: str
    email: str 

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nickname: str = Field(unique=True, nullable=False)
    phone_num: str = Field(nullable=False)
    email: str = Field(nullable=False)
    kakao_id: Optional[str] = None
    profile_image_url: Optional[str] = None
    
    complete_count: int = Field(default=0)
    create_at: datetime = Field(default_factory=datetime.utcnow)
    update_at: datetime = Field(default_factory=datetime.utcnow)