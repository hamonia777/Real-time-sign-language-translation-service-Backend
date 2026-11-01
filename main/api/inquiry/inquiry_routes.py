from fastapi import APIRouter, Depends

from main.core.security import get_current_user_id
from main.domain.Inquiry.dto.inquiry_dto import InquiryCreateRequestDto, InquiryResponseDto, InquiryListResponseDto
from main.domain.Inquiry.usecase.inquiry_usecase import CreateInquiryUseCase, GetMyInquiriesUseCase

router = APIRouter()


@router.post("", response_model=InquiryResponseDto)
def create_inquiry(
    req: InquiryCreateRequestDto,
    usecase: CreateInquiryUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    # 문의는 DB 에만 저장한다. 외부 메신저(카카오 등)로 전송하지 않는다.
    return usecase.execute(user_id, req)


@router.get("", response_model=InquiryListResponseDto)
def my_inquiries(
    usecase: GetMyInquiriesUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    return usecase.execute(user_id)
