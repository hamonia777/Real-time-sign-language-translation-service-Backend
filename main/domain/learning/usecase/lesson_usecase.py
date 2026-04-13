from fastapi import Depends

from main.domain.learning.dto.lesson_dto import (
    LessonListResponseDto,
    LessonResponseDto,
    SaveResultRequestDto,
    SaveResultResponseDto,
    SeedResponseDto,
)
from main.domain.learning.service.lesson_service import LessonService


PASS_THRESHOLD = 80.0


def _to_response(lesson) -> LessonResponseDto:
    return LessonResponseDto(
        lesson_id=lesson.id,
        title=lesson.title,
        category=lesson.category,
        subcategory=lesson.subcategory,
        level=lesson.level,
        video_url=lesson.video_url,
        thumbnail_url=lesson.thumbnail_url,
    )


class GetLessonUseCase:
    def __init__(self, service: LessonService = Depends()):
        self.service = service

    def execute(self, lesson_id: int) -> LessonResponseDto:
        lesson = self.service.get_lesson(lesson_id)
        return _to_response(lesson)


class ListLessonsUseCase:
    def __init__(self, service: LessonService = Depends()):
        self.service = service

    def execute(self, category: str) -> LessonListResponseDto:
        lessons = self.service.list_by_category(category)
        items = [_to_response(l) for l in lessons]
        return LessonListResponseDto(total_count=len(items), items=items)


class SeedFingerspellUseCase:
    def __init__(self, service: LessonService = Depends()):
        self.service = service

    def execute(self) -> SeedResponseDto:
        result = self.service.seed_fingerspell()
        return SeedResponseDto(
            inserted=result["inserted"],
            skipped=result["skipped"],
            total=result["total"],
            message=f"자모음 시드 완료: {result['inserted']}개 추가, {result['skipped']}개 스킵",
        )


class SaveResultUseCase:
    def __init__(self, service: LessonService = Depends()):
        self.service = service

    def execute(self, req: SaveResultRequestDto) -> SaveResultResponseDto:
        # 오늘은 인증 없이 동작 — 결과는 판정만 하고 리턴한다.
        # (USER_LESSON_PROGRESS 저장은 인증 붙는 후속 작업에서 추가)
        self.service.get_lesson(req.lesson_id)
        is_passed = req.score >= PASS_THRESHOLD
        return SaveResultResponseDto(
            lesson_id=req.lesson_id,
            score=req.score,
            is_passed=is_passed,
            attempt=req.attempt,
            pass_threshold=PASS_THRESHOLD,
        )
