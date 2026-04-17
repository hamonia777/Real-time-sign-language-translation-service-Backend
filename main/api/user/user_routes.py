import httpx
from fastapi import APIRouter, Depends, Response, HTTPException
from fastapi.responses import RedirectResponse

from main.core.config import settings
from main.domain.user.dto.user_request_dto import UserSignUpRequestDto, UserInfoRequestDto
from main.domain.user.dto.user_response_dto import UserSignUpResponseDto, KakaoLoginResponseDto
from main.domain.user.usecase.user_usecase import KakaoLoginUseCase, UserProfileUseCase

from main.core.security import create_tokens, get_current_user_id, save_refresh_token, delete_refresh_token

router = APIRouter()

@router.post("/info")
async def update_user_info(
        user_info_req: UserInfoRequestDto,
        usecase: UserProfileUseCase = Depends(),
        user_id: int = Depends(get_current_user_id)
):
    result = await usecase.update_info(user_id, user_info_req)
    return result


@router.get("/login/kakao")
def kakao_login():
    auth_url = (
        f"https://kauth.kakao.com/oauth/authorize?"
        f"client_id={settings.KAKAO_REST_API_KEY}&redirect_uri={settings.KAKAO_REDIRECT_URI}&response_type=code"
    )
    return RedirectResponse(auth_url)


@router.get("/kakao/auth", response_model=KakaoLoginResponseDto)
async def kakao_callback(code: str, response: Response, usecase: KakaoLoginUseCase = Depends()):
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": settings.KAKAO_REST_API_KEY,
        "redirect_uri": settings.KAKAO_REDIRECT_URI,
        "code": code,
        "client_secret": settings.KAKAO_CLIENT_SECRET
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
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8"
        }

        user_response = await client.get(user_info_url, headers=user_info_headers)
        user_info = user_response.json()

    kakao_id = str(user_info.get("id"))

    user = await usecase.execute(kakao_id, user_info)
    my_access_token, my_refresh_token = create_tokens(user.id)
    await save_refresh_token(user.id, my_refresh_token)
    response.headers["Authorization"] = f"Bearer {my_access_token}"

    if(user.phone_num == None):
        check =  True
    else:
        check = False

    response.set_cookie(
        key="refresh_token",
        value=my_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=1209600
    )

    return KakaoLoginResponseDto(
        message="로그인 성공",
        email=user.email,
        is_first=check
    )

@router.get("/logout")
async def logout(
        response: Response,
        user_id: int = Depends(get_current_user_id)
):
    await delete_refresh_token(user_id)

    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="lax"
    )

    return {"message": "성공적으로 로그아웃 되었습니다."}