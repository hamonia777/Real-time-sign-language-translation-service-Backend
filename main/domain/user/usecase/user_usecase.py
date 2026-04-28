# 가령: 26/04/19 수정내용: Kakao 로그인/초기정보 UseCase 복원 (SignUpUseCase 유지 + KakaoLoginUseCase + UserProfileUseCase 추가)
import uuid
from datetime import datetime
from pathlib import Path
from typing import List
from fastapi import Depends, HTTPException, UploadFile

UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "frontend" / "images" / "uploads"

from main.domain.user.dto.user_request_dto import (
    UserSignUpRequestDto,
    UserInfoRequestDto,
)
from main.domain.user.dto.user_dto import UserCreateDomainDto
from main.domain.user.dto.user_response_dto import (
    ProfilePhotoItemDto,
    ProfilePhotoListResponseDto,
    ProfilePhotoResponseDto,
    NicknameResponseDto,
    NicknameCheckResponseDto,
    UserProfileResponseDto,
    UserRankingDto,
)
from main.domain.user.entity.user import User
from main.domain.user.repository.user_repository import (
    UserRepository,
    get_user_repository,
)
from main.domain.user.service.user_service import UserService
from main.domain.ProfilePhoto.entity.profile_photo import ProfilePhoto
from main.domain.ProfilePhoto.repository.profile_photo_repository import (
    ProfilePhotoRepository,
    get_profile_photo_repository,
)

DEFAULT_PHOTOS = [
    {"name": "기본1", "photo_url": "/images/profile_1.png"},
    {"name": "기본2", "photo_url": "/images/profile_2.png"},
    {"name": "기본3", "photo_url": "/images/profile_3.png"},
    {"name": "기본4", "photo_url": "/images/profile_4.png"},
    {"name": "기본5", "photo_url": "/images/profile_5.png"},
]


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

    async def execute(self, kakao_id: str, kakao_user_info: dict, kakao_access_token: str = None, kakao_refresh_token: str = None):
        user = self.user_repo.find_by_kakao_id(kakao_id)
        if user:
            user.kakao_access_token = kakao_access_token
            if kakao_refresh_token:
                user.kakao_refresh_token = kakao_refresh_token
            return self.user_repo.save(user)

        print(f"새로운 카카오 유저입니다. 가입을 진행합니다: {kakao_id}")
        kakao_account = kakao_user_info.get("kakao_account", {})
        properties = kakao_user_info.get("properties", {})

        email = kakao_account.get("email", f"{kakao_id}@kakao.temp.com")
        nickname = properties.get("nickname", f"카카오유저_{kakao_id[-6:]}")

        new_user = User(
            kakao_id=kakao_id,
            email=email,
            nickname=nickname,
            phone_num="",
            kakao_access_token=kakao_access_token,
            kakao_refresh_token=kakao_refresh_token,
        )
        return self.user_repo.save(new_user)

class UserRankUseCase:
    def __init__(self, user_repo: UserRepository = Depends(get_user_repository)):
        self.user_repo = user_repo

    async def get_ranking(self) -> List[UserRankingDto]:
        top_users = self.user_repo.get_top_users_by_complete_count(limit=5)
        
        results = [
            UserRankingDto(
                rank=index + 1,
                userId=user.id,
                nickname=user.nickname or "이름없음",
                profileImageUrl=user.profile_image_url,
                completedLearningCount=user.complete_count
            ) for index, user in enumerate(top_users)
        ]
        
        return results

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


class GetProfilePhotosUseCase:
    def __init__(self, photo_repo: ProfilePhotoRepository = Depends(get_profile_photo_repository)):
        self.photo_repo = photo_repo

    def execute(self) -> ProfilePhotoListResponseDto:
        if self.photo_repo.count() == 0:
            self.photo_repo.save_all([
                ProfilePhoto(photo_url=p["photo_url"], name=p["name"])
                for p in DEFAULT_PHOTOS
            ])
        photos = self.photo_repo.list_all()
        return ProfilePhotoListResponseDto(
            photos=[ProfilePhotoItemDto(photo_id=p.id, photo_url=p.photo_url, name=p.name) for p in photos]
        )


class GetProfilePhotoUseCase:
    def __init__(
        self,
        user_repo: UserRepository = Depends(get_user_repository),
        photo_repo: ProfilePhotoRepository = Depends(get_profile_photo_repository),
    ):
        self.user_repo = user_repo
        self.photo_repo = photo_repo

    def execute(self, user_id: int) -> ProfilePhotoResponseDto:
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
        photo_url = user.profile_image_url or ""
        preset_urls = {p.photo_url for p in self.photo_repo.list_all()}
        photo_type = "preset" if photo_url in preset_urls else "custom"
        return ProfilePhotoResponseDto(user_id=user.id, photo_url=photo_url, photo_type=photo_type)


class UpdateProfilePhotoUseCase:
    def __init__(
        self,
        user_repo: UserRepository = Depends(get_user_repository),
        photo_repo: ProfilePhotoRepository = Depends(get_profile_photo_repository),
    ):
        self.user_repo = user_repo
        self.photo_repo = photo_repo

    def execute(self, user_id: int, photo_id: int) -> ProfilePhotoResponseDto:
        photo = self.photo_repo.find_by_id(photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="해당 프로필 사진을 찾을 수 없습니다.")
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
        user.profile_image_url = photo.photo_url
        user.updated_at = datetime.now()
        self.user_repo.save(user)
        return ProfilePhotoResponseDto(
            user_id=user.id,
            photo_url=photo.photo_url,
            photo_type="preset",
            updated_at=user.updated_at,
        )


class UpdateNicknameUseCase:
    def __init__(self, user_repo: UserRepository = Depends(get_user_repository)):
        self.user_repo = user_repo

    def execute(self, user_id: int, nickname: str) -> NicknameResponseDto:
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

        if user.nickname_updated_at:
            days_passed = (datetime.now() - user.nickname_updated_at).days
            if days_passed < 7:
                days_left = 7 - days_passed
                raise HTTPException(
                    status_code=400,
                    detail=f"닉네임은 변경 후 7일이 지나야 다시 변경할 수 있습니다. ({days_left}일 후 가능)"
                )

        existing = self.user_repo.find_by_nickname(nickname)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=409, detail="이미 사용 중인 닉네임입니다.")

        user.nickname = nickname
        user.updated_at = datetime.now()
        user.nickname_updated_at = datetime.now()
        self.user_repo.save(user)
        return NicknameResponseDto(
            user_id=user.id,
            nickname=user.nickname,
            updated_at=user.updated_at,
            nickname_updated_at=user.nickname_updated_at,
        )


class GetNotificationStatusUseCase:
    def __init__(self, user_repo: UserRepository = Depends(get_user_repository)):
        self.user_repo = user_repo

    def execute(self, user_id: int) -> dict:
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
        return {"enabled": user.kakao_notification_enabled}


class DisableNotificationUseCase:
    def __init__(self, user_repo: UserRepository = Depends(get_user_repository)):
        self.user_repo = user_repo

    def execute(self, user_id: int) -> dict:
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
        user.kakao_notification_enabled = False
        self.user_repo.save(user)
        return {"enabled": False}


class GetUserProfileUseCase:
    def __init__(self, user_repo: UserRepository = Depends(get_user_repository)):
        self.user_repo = user_repo

    def execute(self, user_id: int) -> UserProfileResponseDto:
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
        return UserProfileResponseDto(
            user_id=user.id,
            nickname=user.nickname,
            email=user.email,
            phone_num=user.phone_num,
            nickname_updated_at=user.nickname_updated_at,
        )


class CheckNicknameUseCase:
    def __init__(self, user_repo: UserRepository = Depends(get_user_repository)):
        self.user_repo = user_repo

    def execute(self, nickname: str) -> NicknameCheckResponseDto:
        existing = self.user_repo.find_by_nickname(nickname)
        return NicknameCheckResponseDto(nickname=nickname, is_available=existing is None)


class UploadProfilePhotoUseCase:
    def __init__(self, user_repo: UserRepository = Depends(get_user_repository)):
        self.user_repo = user_repo

    async def execute(self, user_id: int, file: UploadFile) -> ProfilePhotoResponseDto:
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

        ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
        filename = f"{user_id}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = UPLOADS_DIR / filename

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        photo_url = f"/images/uploads/{filename}"
        user.profile_image_url = photo_url
        user.updated_at = datetime.now()
        self.user_repo.save(user)

        return ProfilePhotoResponseDto(
            user_id=user.id,
            photo_url=photo_url,
            photo_type="custom",
            updated_at=user.updated_at,
        )