from pydantic import BaseModel

class UserSignUpResponseDto(BaseModel):
    message: str
    nickname: str 