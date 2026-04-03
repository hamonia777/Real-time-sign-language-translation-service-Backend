from pydantic import BaseModel, EmailStr, Field

class UserSignUpRequestDto(BaseModel):
    email: EmailStr 
    nickname: str = Field(..., min_length=2, max_length=20)
    phone_number: str = Field(..., pattern=r'^\d{3}-\d{3,4}-\d{4}$')