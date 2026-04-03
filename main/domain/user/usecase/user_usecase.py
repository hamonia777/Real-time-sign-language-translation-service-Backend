from main.domain.user.dto.user_request_dto import UserSignUpRequestDto
from main.domain.user.dto.user_dto import UserCreateDomainDto
from main.domain.user.service.user_service import UserService
from fastapi import Depends

class SignUpUseCase:
    def __init__(self, user_service: UserService = Depends()):
        self.user_service = user_service

    def execute(self, request_dto: UserSignUpRequestDto):
        domain_dto = UserCreateDomainDto(
            email=request_dto.email,
            nickname=request_dto.nickname,
            phone_number=request_dto.phone_number
        )

        created_user = self.user_service.create_user(domain_dto)

        return created_user