import json
import httpx
from main.core.config import settings


async def refresh_kakao_token(refresh_token: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "refresh_token",
                "client_id": settings.KAKAO_REST_API_KEY,
                "refresh_token": refresh_token,
                "client_secret": settings.KAKAO_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
        )
        data = res.json()
        return data if "access_token" in data else None


async def send_kakao_message(access_token: str, nickname: str) -> bool:
    template = {
        "object_type": "text",
        "text": (
            f"안녕하세요 {nickname or ''}님! 📚\n"
            "오늘 아직 수어 학습을 하지 않으셨어요.\n"
            "하루 1학습으로 꾸준히 실력을 키워보세요! 🤟"
        ),
        "link": {
            "web_url": "http://localhost:8080/learning.html",
            "mobile_web_url": "http://localhost:8080/learning.html",
        },
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://kapi.kakao.com/v2/api/talk/memo/default/send",
            data={"template_object": json.dumps(template, ensure_ascii=False)},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
            },
        )
        result = res.json()
        return result.get("result_code") == 0
