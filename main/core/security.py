import jwt
from datetime import datetime, timedelta, timezone
from main.core.config import settings
from main.core.redis_client import redis_client

def create_tokens(user_id: str | int) -> tuple[str, str]:
    
    access_expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_payload = {
        "sub": str(user_id),
        "exp": access_expire
    }
    access_token = jwt.encode(access_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    refresh_expire = datetime.now(timezone.utc) + timedelta(days=14)
    refresh_payload = {
        "sub": str(user_id),
        "exp": refresh_expire
    }
    refresh_token = jwt.encode(refresh_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return access_token, refresh_token


async def save_refresh_token(user_id: str | int, refresh_token: str):
    
    # 14일
    expire_seconds = 14 * 24 * 60 * 60 
    
    await redis_client.set(
        name=f"RT:{user_id}",
        value=refresh_token,
        ex=expire_seconds 
    )