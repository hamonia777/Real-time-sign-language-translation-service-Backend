from datetime import datetime
from pydantic import BaseModel


class InquiryCreateRequestDto(BaseModel):
    title: str
    content: str
    marketing_agree: bool = False


class InquiryResponseDto(BaseModel):
    id: int
    user_id: int
    title: str | None
    content: str | None
    created_at: datetime


class InquiryListResponseDto(BaseModel):
    inquiries: list[InquiryResponseDto]
    total: int
