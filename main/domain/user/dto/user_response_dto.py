# 가령: 26/04/19 수정내용: 병합 후 누락된 KakaoLoginResponseDto 복원
from pydantic import BaseModel


class UserSignUpResponseDto(BaseModel):
    message: str
    nickname: str


class KakaoLoginResponseDto(BaseModel):
    message: str
    email: str | None = None
    is_first: bool = False
