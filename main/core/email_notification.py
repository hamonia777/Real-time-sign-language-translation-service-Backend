import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from main.core.config import settings


def _send_email_sync(to_email: str, nickname: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📚 오늘 수어 학습을 잊지 않으셨나요?"
    msg["From"] = settings.EMAIL_SENDER
    msg["To"] = to_email

    body = f"""\
안녕하세요 {nickname or ''}님! 👋

오늘 아직 수어 학습을 하지 않으셨어요.
하루 1학습으로 꾸준히 실력을 키워보세요! 🤟

👉 학습하러 가기: http://localhost:8080/learning.html

수어 연구소 드림
"""
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.naver.com", 465) as server:
        server.login(settings.EMAIL_SENDER, settings.EMAIL_PASSWORD)
        server.sendmail(settings.EMAIL_SENDER, to_email, msg.as_string())


async def send_learning_reminder_email(to_email: str, nickname: str) -> tuple[bool, str]:
    try:
        await asyncio.to_thread(_send_email_sync, to_email, nickname)
        return True, ""
    except Exception as e:
        print(f"[이메일 발송 실패] {to_email}: {e}")
        return False, str(e)
