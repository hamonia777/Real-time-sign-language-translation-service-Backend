from main.domain.user.dto.user_request_dto import UserSignUpRequestDto
from main.domain.user.dto.user_dto import UserCreateDomainDto
from main.domain.user.service.user_service import UserService
from main.domain.user.repository.user_repository import UserRepository, get_user_repository
from fastapi import Depends
from main.domain.user.entity.user import User

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
    
class KakaoLoginUseCase:
    def __init__(self, user_repo: UserRepository = Depends(get_user_repository)):
        self.user_repo = user_repo

    def execute(self, kakao_id: str, kakao_user_info: dict):

        user = self.user_repo.find_by_kakao_id(kakao_id)
        
        if user:
            return user
        print(f"새로운 카카오 유저입니다. 가입을 진행합니다: {kakao_id}")
        kakao_account = kakao_user_info.get("kakao_account", {})
        properties = kakao_user_info.get("properties", {})
        
        email = kakao_account.get("email", f"{kakao_id}@kakao.temp.com")
        nickname = properties.get("nickname", "카카오유저")
        
        new_user = User(
            kakao_id=kakao_id,
            email=email,
            nickname=nickname,
        )
        saved_user = self.user_repo.save(new_user)
        return saved_user            
