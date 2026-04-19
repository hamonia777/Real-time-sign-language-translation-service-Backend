# 가령: 26/04/19 수정내용: Kakao 로그인/초기정보 UseCase 복원 (SignUpUseCase 유지 + KakaoLoginUseCase + UserProfileUseCase 추가)
from fastapi import Depends, HTTPException

from main.domain.user.dto.user_request_dto import (
    UserSignUpRequestDto,
    UserInfoRequestDto,
)
from main.domain.user.dto.user_dto import UserCreateDomainDto
from main.domain.user.entity.user import User
from main.domain.user.repository.user_repository import (
    UserRepository,
    get_user_repository,
)
from main.domain.user.service.user_service import UserService


class SignUpUseCase:
    def __init__(self, user_service: UserService = Depends()):
        self.user_service = user_service

    def execute(self, request_dto: UserSignUpRequestDto):
        domain_dto = UserCreateDomainDto(
            email=request_dto.email,
            nickname=request_dto.nickname,
            phone_number=request_dto.phone_number,
        )
        created_user = self.user_service.create_user(domain_dto)
        return created_user


class KakaoLoginUseCase:
    def __init__(self, user_repo: UserRepository = Depends(get_user_repository)):
        self.user_repo = user_repo

    async def execute(self, kakao_id: str, kakao_user_info: dict):
        user = self.user_repo.find_by_kakao_id(kakao_id)
        if user:
            return user

        print(f"새로운 카카오 유저입니다. 가입을 진행합니다: {kakao_id}")
        kakao_account = kakao_user_info.get("kakao_account", {})
        properties = kakao_user_info.get("properties", {})

        email = kakao_account.get("email", f"{kakao_id}@kakao.temp.com")
        nickname = properties.get("nickname", f"카카오유저_{kakao_id[-6:]}")

        new_user = User(
            kakao_id=kakao_id,
            email=email,
            nickname=nickname,
            phone_num="",  # 초기 정보 입력 전 임시값
        )
        return self.user_repo.save(new_user)


class UserProfileUseCase:
    def __init__(self, user_repo: UserRepository = Depends(get_user_repository)):
        self.user_repo = user_repo

    async def update_info(self, user_id: int, req: UserInfoRequestDto):
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

        user.nickname = req.name
        user.phone_num = req.phone_num
        user.email = req.email

        self.user_repo.save(user)
        return {"msg": "초기 정보 입력 완료"}
