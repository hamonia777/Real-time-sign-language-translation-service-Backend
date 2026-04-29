"""
sign_words_video.json의 영상 URL을 lessons 테이블에 업데이트하는 스크립트
사용법: python update_video_urls.py
"""

import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# 모든 모델 import (관계 해결을 위해 필요)
from main.domain.user.entity.user import User  # noqa
from main.domain.learning.entity.lesson import Lesson  # noqa
from main.domain.LearningBasket.entity.learning_basket import LearningBasket  # noqa
from main.domain.UserLessonProgress.entity.user_lesson_progress import UserLessonProgress  # noqa
from main.domain.UserSurveyProfiles.entity.user_survey_profiles import UserSurveyProfile  # noqa
from main.domain.Inquiry.entity.inquiry import Inquiry  # noqa
from main.domain.StudyLog.entity.study_log import StudyLog  # noqa
from main.domain.LessonWordMapping.entity.lesson_word_mapping import LessonWordMapping  # noqa

from sqlmodel import Session, create_engine, select
from main.core.config import settings

engine = create_engine(
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)


def update_video_urls():
    with open("sign_words_video.json", "r", encoding="utf-8") as f:
        video_data = json.load(f)

    video_map = {item["word"]: item["video_url"] for item in video_data}
    print(f"JSON 파일: {len(video_map)}개 단어\n")

    success = 0
    failed = []

    with Session(engine) as session:
        lessons = session.exec(select(Lesson)).all()
        print(f"DB 레슨: {len(lessons)}개\n")

        for lesson in lessons:
            title = lesson.title
            matched = False

            # 1. 정확히 일치
            if title in video_map:
                lesson.video_url = video_map[title]
                session.add(lesson)
                success += 1
                print(f"O '{title}'")
                matched = True

            # 2. 슬래시 구분 (예: 아버지/아빠)
            if not matched:
                for part in title.split("/"):
                    part = part.strip()
                    if part in video_map:
                        lesson.video_url = video_map[part]
                        session.add(lesson)
                        success += 1
                        print(f"O '{title}' → '{part}'로 매칭")
                        matched = True
                        break

            # 3. 쉼표 구분 (예: 맞다,사실)
            if not matched:
                for part in title.split(","):
                    part = part.strip()
                    if part in video_map:
                        lesson.video_url = video_map[part]
                        session.add(lesson)
                        success += 1
                        print(f"O '{title}' → '{part}'로 매칭")
                        matched = True
                        break

            if not matched:
                failed.append(title)
                print(f"X '{title}'")

        session.commit()

    print(f"\n 완료! 성공: {success}개 / 실패: {len(failed)}개")
    if failed:
        print(f"\n실패 목록: {failed}")


if __name__ == "__main__":
    update_video_urls()