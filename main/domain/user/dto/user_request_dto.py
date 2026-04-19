# 가령: 26/04/19 수정내용: 병합 후 누락된 UserInfoRequestDto 복원 (초기 정보 입력 /info 용)
from pydantic import BaseModel, EmailStr, Field


class UserSignUpRequestDto(BaseModel):
    email: EmailStr
    nickname: str = Field(..., min_length=2, max_length=20)
    phone_number: str = Field(..., pattern=r'^\d{3}-\d{3,4}-\d{4}$')


class UserInfoRequestDto(BaseModel):
    name: str
    phone_num: str
    email: str
