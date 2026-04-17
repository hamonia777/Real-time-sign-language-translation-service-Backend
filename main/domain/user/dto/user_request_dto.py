from pydantic import BaseModel, EmailStr, Field

class UserSignUpRequestDto(BaseModel):
    email: EmailStr 
    name: str = Field(..., min_length=2, max_length=20)
    phone: str = Field(..., pattern=r'^\d{3}-\d{3,4}-\d{4}$')

class UserInfoRequestDto(BaseModel):
    name: str
    phone_num: str
    email: str