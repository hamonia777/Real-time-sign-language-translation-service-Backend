from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import Session, select

from main.core.database import engine
from main.core.email_notification import send_learning_reminder_email
from main.domain.user.entity.user import User
from main.domain.StudyLog.entity.study_log import StudyLog

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


async def send_daily_learning_reminders():
    print("[스케줄러] 미학습자 이메일 알림 발송 시작")
    today = date.today()

    with Session(engine) as session:
        studied_ids = session.exec(
            select(StudyLog.user_id).where(StudyLog.study_date == today)
        ).all()

        query = select(User).where(
            User.kakao_notification_enabled == True,
            User.email != None,
        )
        if studied_ids:
            query = query.where(User.id.not_in(studied_ids))
        users = session.exec(query).all()

        print(f"[스케줄러] 알림 대상: {len(users)}명")

        for user in users:
            if user.email:
                success, _ = await send_learning_reminder_email(user.email, user.nickname)
                status = "✅" if success else "❌"
                print(f"  {status} {user.email}")

    print("[스케줄러] 알림 발송 완료")


def start_scheduler():
    scheduler.add_job(
        send_daily_learning_reminders,
        trigger="cron",
        hour=20,
        minute=0,
        id="daily_learning_reminder",
    )
    scheduler.start()
    print("[스케줄러] 시작 — 매일 오후 8시 이메일 알림 예약")
