from fastapi import APIRouter, Depends
from main.domain.user.dto.user_request_dto import UserSignUpRequestDto
from main.domain.user.dto.user_response_dto import UserSignUpResponseDto 
from main.domain.user.usecase.user_usecase import SignUpUseCase 

router = APIRouter()

@router.post("/sign-up", response_model=UserSignUpResponseDto)
def create_user(
    user_req: UserSignUpRequestDto, 
    usecase: SignUpUseCase = Depends()
):
    result_user = usecase.execute(user_req)
    
    return UserSignUpResponseDto(
        message="회원가입이 완료되었습니다.",
        nickname=result_user.nickname
    )