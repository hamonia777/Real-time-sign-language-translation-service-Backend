# 가령: 26/04/19 수정내용: 병합으로 삭제된 JWT/Refresh token 보안 모듈 복구
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from main.core.config import settings
from main.core.redis_client import redis_client

security = HTTPBearer()


def create_tokens(user_id: str | int) -> tuple[str, str]:
    access_expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_payload = {"sub": str(user_id), "exp": access_expire}
    access_token = jwt.encode(
        access_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    refresh_expire = datetime.now(timezone.utc) + timedelta(days=14)
    refresh_payload = {"sub": str(user_id), "exp": refresh_expire}
    refresh_token = jwt.encode(
        refresh_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    return access_token, refresh_token


async def save_refresh_token(user_id: str | int, refresh_token: str):
    try:
        expire_seconds = 14 * 24 * 60 * 60
        await redis_client.set(
            name=f"RT:{user_id}",
            value=refresh_token,
            ex=expire_seconds,
        )
    except Exception:
        pass


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        return int(user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="토큰 검증에 실패했습니다.")


async def delete_refresh_token(user_id: int):
    try:
        redis_key = f"RT:{user_id}"
        await redis_client.delete(redis_key)
    except Exception:
        pass