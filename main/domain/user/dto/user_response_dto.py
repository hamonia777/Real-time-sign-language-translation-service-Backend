from pydantic import BaseModel

class UserSignUpResponseDto(BaseModel):
    message: str
    nickname: str

class KakaoLoginResponseDto(BaseModel):
    message: str
    email: str
    is_first: bool

class KakaoLogoutResponseDto(BaseModel):
    message: str   