# 가령: 26/04/19 수정내용: git 충돌 해결 — 기존 /sign-up (upstream) + Kakao 로그인/콜백/로그아웃 (stash) 양쪽 모두 유지
import httpx
import traceback
from typing import List
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
    UserRankingDto,
)
from main.domain.user.usecase.user_usecase import (
    SignUpUseCase,
    KakaoLoginUseCase,
    UserProfileUseCase,
    UserRankUseCase,
)

router = APIRouter()


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
        f"client_id={settings.KAKAO_REST_API_KEY}&redirect_uri={settings.KAKAO_REDIRECT_URI}"
        f"&response_type=code"
    )
    return RedirectResponse(auth_url)


@router.get("/kakao/notification/enable")
def kakao_notification_enable():
    """학습 알림 ON 시 talk_message 동의 페이지로 이동"""
    auth_url = (
        f"https://kauth.kakao.com/oauth/authorize?"
        f"client_id={settings.KAKAO_REST_API_KEY}&redirect_uri={settings.KAKAO_REDIRECT_URI}"
        f"&response_type=code&scope=talk_message&state=notification&prompt=consent"
    )
    return RedirectResponse(auth_url)


@router.get("/kakao/auth", response_model=KakaoLoginResponseDto)
async def kakao_callback(
    code: str,
    response: Response,
    usecase: KakaoLoginUseCase = Depends(),
    state: str = None,
):
    try:
        if state == "notification":
            return await _kakao_notification_consent_impl(code, usecase)
        return await _kakao_callback_impl(code, response, usecase)
    except Exception as e:
        print("===== 카카오 콜백 에러 =====")
        print(traceback.format_exc())
        print("===========================")
        raise


async def _kakao_notification_consent_impl(code: str, usecase: KakaoLoginUseCase):
    """토글 ON 후 카카오 동의 완료 → 토큰 저장 + notification_enabled = True"""
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": settings.KAKAO_REST_API_KEY,
        "redirect_uri": settings.KAKAO_REDIRECT_URI,
        "code": code,
        "client_secret": settings.KAKAO_CLIENT_SECRET,
    }
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            token_url,
            data=token_data,
            headers={"Content-type": "application/x-www-form-urlencoded;charset=utf-8"},
        )
        token_json = token_response.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="토큰 발급 실패")

        kakao_refresh_token = token_json.get("refresh_token")

        user_info_res = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        kakao_id = str(user_info_res.json().get("id"))

    user = usecase.user_repo.find_by_kakao_id(kakao_id)
    if user:
        user.kakao_access_token = access_token
        if kakao_refresh_token:
            user.kakao_refresh_token = kakao_refresh_token
        user.kakao_notification_enabled = True
        usecase.user_repo.save(user)

    return RedirectResponse(url="/mypage.html", status_code=302)


async def _kakao_callback_impl(code: str, response: Response, usecase: KakaoLoginUseCase):
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
            print(f"[카카오 토큰 실패] 응답: {token_json}")
            raise HTTPException(status_code=400, detail=f"토큰 발급 실패: {token_json.get('error_code', '')} {token_json.get('error_description', '')}")

        kakao_refresh_token = token_json.get("refresh_token")

        user_info_url = "https://kapi.kakao.com/v2/user/me"
        user_info_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
        }
        user_response = await client.get(user_info_url, headers=user_info_headers)
        user_info = user_response.json()

    kakao_id = str(user_info.get("id"))

    user = await usecase.execute(kakao_id, user_info, kakao_access_token=access_token, kakao_refresh_token=kakao_refresh_token)
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

    #return KakaoLoginResponseDto(
    #    message="로그인 성공",
    #    email=user.email,
    #    is_first=is_first,
    #)

    # 혜미 : 26/04/20 수정내용 : 사용자 입장에서는 JSON 응답보다 로그인 후 리다이렉트가 더 자연스러울 것 같아서, 로그인 성공 시 프론트엔드의 /register.html (전화번호 입력 페이지) 또는 / (메인 페이지)로 리다이렉트하도록 변경
    if is_first:
        redirect = RedirectResponse(url="/register.html", status_code=302)
    else:
        redirect = RedirectResponse(url="/", status_code=302)

    redirect.set_cookie(key="refresh_token", value=my_refresh_token, httponly=True, secure=False, samesite="lax", max_age=1209600)
    redirect.set_cookie(key="access_token", value=my_access_token, httponly=False, secure=False, samesite="lax", max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    redirect.headers["Authorization"] = f"Bearer {my_access_token}"
    return redirect



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

@router.get("/ranking", response_model=List[UserRankingDto])
async def get_user_ranking(
    usecase: UserRankUseCase = Depends()
):
    return await usecase.get_ranking()