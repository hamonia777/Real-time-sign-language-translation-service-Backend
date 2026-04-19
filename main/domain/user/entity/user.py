from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

class UserSignUpDto(SQLModel):
    nickname: str
    phone_num: str
    email: str 

# 가령: 26/04/19 수정내용: Kakao 로그인 초기 상태(전화번호 미입력) 대응 위해 phone_num, nickname 을 Optional 로 변경
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    nickname: Optional[str] = Field(default=None)
    phone_num: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    kakao_id: Optional[str] = None
    profile_image_url: Optional[str] = None

    complete_count: int = Field(default=0)
    create_at: datetime = Field(default_factory=datetime.utcnow)
    update_at: datetime = Field(default_factory=datetime.utcnow)