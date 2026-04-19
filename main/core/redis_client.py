# 가령: 26/04/19 수정내용: 병합으로 삭제된 Redis 클라이언트 복구
import redis.asyncio as redis
from main.core.config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True,
)