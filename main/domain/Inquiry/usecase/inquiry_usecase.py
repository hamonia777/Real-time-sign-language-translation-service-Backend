from fastapi import Depends, HTTPException

from main.domain.Inquiry.dto.inquiry_dto import (
    InquiryCreateRequestDto,
    InquiryResponseDto,
    InquiryListResponseDto,
)
from main.domain.Inquiry.entity.inquiry import Inquiry
from main.domain.Inquiry.repository.inquiry_repository import (
    InquiryRepository,
    get_inquiry_repository,
)


class CreateInquiryUseCase:
    def __init__(self, repo: InquiryRepository = Depends(get_inquiry_repository)):
        self.repo = repo

    def execute(self, user_id: int, req: InquiryCreateRequestDto) -> InquiryResponseDto:
        inquiry = Inquiry(
            user_id=user_id,
            title=req.title,
            content=req.content,
        )
        saved = self.repo.save(inquiry)
        return InquiryResponseDto(
            id=saved.id,
            user_id=saved.user_id,
            title=saved.title,
            content=saved.content,
            created_at=saved.created_at,
        )


class GetMyInquiriesUseCase:
    def __init__(self, repo: InquiryRepository = Depends(get_inquiry_repository)):
        self.repo = repo

    def execute(self, user_id: int) -> InquiryListResponseDto:
        inquiries = self.repo.find_by_user_id(user_id)
        items = [
            InquiryResponseDto(
                id=i.id,
                user_id=i.user_id,
                title=i.title,
                content=i.content,
                created_at=i.created_at,
            )
            for i in inquiries
        ]
        return InquiryListResponseDto(inquiries=items, total=len(items))
