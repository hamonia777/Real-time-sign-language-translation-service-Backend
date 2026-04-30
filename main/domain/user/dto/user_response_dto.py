from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

# 가령: 26/04/19 수정내용: Kakao 로그인 Nullable 이메일 처리 방어(learning) + 로그아웃 DTO 추가(master) 병합


class UserSignUpResponseDto(BaseModel):
    message: str
    nickname: str


class UserRankingDto(BaseModel):
    rank: int
    userId: int
    nickname: Optional[str] = None
    profileImageUrl: Optional[str] = None
    completedLearningCount: int


class KakaoLoginResponseDto(BaseModel):
    message: str
    email: Optional[str] = None
    is_first: bool = False


class KakaoLogoutResponseDto(BaseModel):
    message: str


class ProfilePhotoItemDto(BaseModel):
    photo_id: int
    photo_url: str
    name: str


class ProfilePhotoListResponseDto(BaseModel):
    photos: List[ProfilePhotoItemDto]


class ProfilePhotoResponseDto(BaseModel):
    user_id: int
    photo_url: str
    photo_type: str
    updated_at: Optional[datetime] = None


class NicknameResponseDto(BaseModel):
    user_id: int
    nickname: str
    updated_at: Optional[datetime] = None
    nickname_updated_at: Optional[datetime] = None


class NicknameCheckResponseDto(BaseModel):
    nickname: str
    is_available: bool


class UserProfileResponseDto(BaseModel):
    user_id: int
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone_num: Optional[str] = None
    nickname_updated_at: Optional[datetime] = None
