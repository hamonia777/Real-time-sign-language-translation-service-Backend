from main.domain.UserSurveyProfiles.entity.user_survey_profiles import UserSurveyProfile
from main.domain.user.dto.user_request_dto import UserInfoRequestDto, UserSignUpRequestDto
from main.domain.user.dto.user_dto import UserCreateDomainDto
from main.domain.user.service.user_service import UserService
from main.domain.user.repository.user_repository import UserRepository, get_user_repository
from fastapi import Depends
from fastapi import HTTPException
from main.domain.user.entity.user import User

class UserProfileUseCase:
    def __init__(self, user_repo: UserRepository = Depends(get_user_repository)):
        self.user_repo = user_repo

    async def update_info(self, user_id: int, req: UserInfoRequestDto):
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

        user.nickname = req.name 
        user.phone_num = req.phone_num
        user.email = req.email
        
        await self.user_repo.save(user)
        return {"msg": "초기 정보 입력 완료"}
    
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
        nickname = properties.get("nickname", "카카오유저")
        
        new_user = User(
            kakao_id=kakao_id,
            email=email,
            nickname=nickname,
        )
        saved_user = await self.user_repo.save(new_user)
        return saved_user