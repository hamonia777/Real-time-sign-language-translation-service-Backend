from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from main.core.security import get_current_user_id
# 26.4.30 : 가령 : 수정 내용 - 마이페이지 학습 바구니 조회용 DTO/UseCase import 추가
from main.domain.LearningBasket.dto.learning_basket_dto import (
    LearningBasketListResponseDto,
)
from main.domain.LearningBasket.usecase.learning_basket_usecase import (
    ListLearningBasketUseCase,
)
from main.domain.learning.dto.lesson_dto import (
    AchievementResponseDto,
    LearningProgressListResponseDto,
)
from main.domain.learning.usecase.lesson_usecase import (
    GetMyAchievementUseCase,
    GetMyLearningProgressUseCase,
)
from main.domain.user.dto.user_request_dto import NicknameUpdateRequestDto
from main.domain.user.dto.user_response_dto import (
    ProfilePhotoResponseDto,
    NicknameResponseDto,
    NicknameCheckResponseDto,
    UserProfileResponseDto,
)
from main.domain.user.usecase.user_usecase import (
    GetProfilePhotoUseCase,
    UploadProfilePhotoUseCase,
    UpdateNicknameUseCase,
    CheckNicknameUseCase,
    GetUserProfileUseCase,
    GetNotificationStatusUseCase,
    DisableNotificationUseCase,
)

router = APIRouter()


@router.get("/me", response_model=UserProfileResponseDto)
def get_my_profile(
    usecase: GetUserProfileUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    return usecase.execute(user_id)


@router.get("/photo", response_model=ProfilePhotoResponseDto)
def get_profile_photo(
    usecase: GetProfilePhotoUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    return usecase.execute(user_id)


@router.patch("/photo", response_model=ProfilePhotoResponseDto)
async def update_profile_photo(
    file: UploadFile = File(...),
    usecase: UploadProfilePhotoUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    return await usecase.execute(user_id, file)


@router.patch("/nickname", response_model=NicknameResponseDto)
def update_nickname(
    body: NicknameUpdateRequestDto,
    usecase: UpdateNicknameUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    return usecase.execute(user_id, body.nickname)


@router.get("/nickname/check", response_model=NicknameCheckResponseDto)
def check_nickname(
    nickname: str = Query(..., min_length=2, max_length=8),
    usecase: CheckNicknameUseCase = Depends(),
):
    return usecase.execute(nickname)


@router.get("/notification/status")
def get_notification_status(
    usecase: GetNotificationStatusUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    return usecase.execute(user_id)


@router.get("/learning/completed", response_model=LearningProgressListResponseDto)
def get_completed_learning(
    usecase: GetMyLearningProgressUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    result = usecase.execute(user_id)
    return LearningProgressListResponseDto(
        total_count=result.completed_count,
        items=result.completed,
    )


@router.get("/learning/in-progress", response_model=LearningProgressListResponseDto)
def get_in_progress_learning(
    usecase: GetMyLearningProgressUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    result = usecase.execute(user_id)
    return LearningProgressListResponseDto(
        total_count=result.in_progress_count,
        items=result.in_progress,
    )


@router.get("/achievement", response_model=AchievementResponseDto)
def get_achievement(
    usecase: GetMyAchievementUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    return usecase.execute(user_id)


# 26.4.30 : 가령 : 수정 내용 - 마이페이지 학습 바구니 조회 엔드포인트 신규 추가
@router.get("/basket", response_model=LearningBasketListResponseDto)
def get_learning_basket(
    usecase: ListLearningBasketUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    return usecase.execute(user_id)


@router.patch("/notification/disable")
def disable_notification(
    usecase: DisableNotificationUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    return usecase.execute(user_id)


@router.post("/notification/test")
async def test_notification(
    usecase: GetUserProfileUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    from main.core.email_notification import send_learning_reminder_email

    user = usecase.user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    if not user.email:
        raise HTTPException(status_code=400, detail="이메일 정보가 없습니다.")

    success, error = await send_learning_reminder_email(user.email, user.nickname)
    if success:
        return {"result": f"✅ 이메일 발송 성공! {user.email} 을 확인해주세요."}
    return {"result": f"❌ 발송 실패: {error}"}
