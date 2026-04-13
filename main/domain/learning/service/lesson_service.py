from typing import List, Optional

from fastapi import Depends, HTTPException

from main.domain.learning.entity.lesson import Lesson
from main.domain.learning.repository.lesson_repository import (
    LessonRepository,
    get_lesson_repository,
)


KOREAN_CONSONANTS = [
    "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ",
    "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
]

KOREAN_VOWELS = [
    "ㅏ", "ㅑ", "ㅓ", "ㅕ", "ㅗ", "ㅛ", "ㅜ",
    "ㅠ", "ㅡ", "ㅣ", "ㅐ", "ㅒ", "ㅔ", "ㅖ",
]


class LessonService:
    def __init__(self, repo: LessonRepository = Depends(get_lesson_repository)):
        self.repo = repo

    def get_lesson(self, lesson_id: int) -> Lesson:
        lesson = self.repo.find_by_id(lesson_id)
        if lesson is None:
            raise HTTPException(status_code=404, detail="lesson not found")
        return lesson

    def list_by_category(self, category: str) -> List[Lesson]:
        return self.repo.find_by_category(category)

    def seed_fingerspell(self) -> dict:
        inserted = 0
        skipped = 0

        for title in KOREAN_CONSONANTS:
            if self.repo.find_by_title_and_category(title, "fingerspell"):
                skipped += 1
                continue
            self.repo.save(
                Lesson(
                    title=title,
                    category="fingerspell",
                    subcategory="consonant",
                    level=1,
                    video_url="",
                    thumbnail_url=None,
                )
            )
            inserted += 1

        for title in KOREAN_VOWELS:
            if self.repo.find_by_title_and_category(title, "fingerspell"):
                skipped += 1
                continue
            self.repo.save(
                Lesson(
                    title=title,
                    category="fingerspell",
                    subcategory="vowel",
                    level=1,
                    video_url="",
                    thumbnail_url=None,
                )
            )
            inserted += 1

        total = len(KOREAN_CONSONANTS) + len(KOREAN_VOWELS)
        return {"inserted": inserted, "skipped": skipped, "total": total}
