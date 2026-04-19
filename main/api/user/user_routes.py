# 가령: 26/04/19 수정내용: git 충돌 해결 — 기존 /sign-up (upstream) + Kakao 로그인/콜백/로그아웃 (stash) 양쪽 모두 유지
import httpx
from fastapi import APIRouter, Depends, Response, HTTPException
from fastapi.responses import RedirectResponse

from main.core.config import settings
from main.core.security import (
    create_tokens,
    get_current_user_id,
    save_refresh_token,
    delete_refresh_token,
)
from main.domain.user.dto.user_request_dto import (
    UserSignUpRequestDto,
    UserInfoRequestDto,
)
from main.domain.user.dto.user_response_dto import (
    UserSignUpResponseDto,
    KakaoLoginResponseDto,
)
from main.domain.user.usecase.user_usecase import (
    SignUpUseCase,
    KakaoLoginUseCase,
    UserProfileUseCase,
)

router = APIRouter()


@router.post("/sign-up", response_model=UserSignUpResponseDto)
def create_user(
    user_req: UserSignUpRequestDto,
    usecase: SignUpUseCase = Depends(),
):
    result_user = usecase.execute(user_req)
    return UserSignUpResponseDto(
        message="회원가입이 완료되었습니다.",
        nickname=result_user.nickname,
    )


@router.post("/info")
async def update_user_info(
    user_info_req: UserInfoRequestDto,
    usecase: UserProfileUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    return await usecase.update_info(user_id, user_info_req)


@router.get("/login/kakao")
def kakao_login():
    auth_url = (
        f"https://kauth.kakao.com/oauth/authorize?"
        f"client_id={settings.KAKAO_REST_API_KEY}&redirect_uri={settings.KAKAO_REDIRECT_URI}&response_type=code"
    )
    return RedirectResponse(auth_url)


@router.get("/kakao/auth", response_model=KakaoLoginResponseDto)
async def kakao_callback(
    code: str,
    response: Response,
    usecase: KakaoLoginUseCase = Depends(),
):
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": settings.KAKAO_REST_API_KEY,
        "redirect_uri": settings.KAKAO_REDIRECT_URI,
        "code": code,
        "client_secret": settings.KAKAO_CLIENT_SECRET,
    }
    token_headers = {"Content-type": "application/x-www-form-urlencoded;charset=utf-8"}

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data, headers=token_headers)
        token_json = token_response.json()

        access_token = token_json.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="토큰 발급에 실패했습니다.")

        user_info_url = "https://kapi.kakao.com/v2/user/me"
        user_info_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
        }
        user_response = await client.get(user_info_url, headers=user_info_headers)
        user_info = user_response.json()

    kakao_id = str(user_info.get("id"))

    user = await usecase.execute(kakao_id, user_info)
    my_access_token, my_refresh_token = create_tokens(user.id)
    await save_refresh_token(user.id, my_refresh_token)
    response.headers["Authorization"] = f"Bearer {my_access_token}"

    is_first = user.phone_num is None or user.phone_num == ""

    response.set_cookie(
        key="refresh_token",
        value=my_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=1209600,
    )

    # 가령: 26/04/19 수정내용: 프론트엔드 JS 가 읽을 수 있도록 access_token 을 non-httpOnly 쿠키로 저장
    response.set_cookie(
        key="access_token",
        value=my_access_token,
        httponly=False,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return KakaoLoginResponseDto(
        message="로그인 성공",
        email=user.email,
        is_first=is_first,
    )


@router.get("/logout")
async def logout(
    response: Response,
    user_id: int = Depends(get_current_user_id),
):
    await delete_refresh_token(user_id)
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return {"message": "성공적으로 로그아웃 되었습니다."}
