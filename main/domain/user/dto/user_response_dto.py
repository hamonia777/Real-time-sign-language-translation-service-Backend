# 가령: 26/04/19 수정내용: Kakao 로그인 Nullable 이메일 처리 방어(learning) + 로그아웃 DTO 추가(master) 병합
from pydantic import BaseModel


class UserSignUpResponseDto(BaseModel):
    message: str
    nickname: str


class KakaoLoginResponseDto(BaseModel):
    message: str
    email: str | None = None
    is_first: bool = False


class KakaoLogoutResponseDto(BaseModel):
    message: str