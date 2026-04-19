# 가령: 26/04/19 수정내용: SaveResultUseCase 가 user_id 를 받아 user_lesson_progress 에 upsert 하도록 변경
from datetime import datetime

from fastapi import Depends

from main.domain.UserLessonProgress.entity.user_lesson_progress import UserLessonProgress
from main.domain.UserLessonProgress.repository.user_lesson_progress_repository import (
    UserLessonProgressRepository,
    get_user_lesson_progress_repository,
)
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


# 가령: 26/04/19 수정내용: 단어 시드 usecase (insert 외에 기존 row 의 subcategory 업데이트 카운트도 메시지에 포함)
class SeedWordsUseCase:
    def __init__(self, service: LessonService = Depends()):
        self.service = service

    def execute(self) -> SeedResponseDto:
        result = self.service.seed_words()
        updated = result.get("updated", 0)
        return SeedResponseDto(
            inserted=result["inserted"],
            skipped=result["skipped"],
            total=result["total"],
            message=(
                f"단어 시드 완료: {result['inserted']}개 추가, "
                f"{updated}개 카테고리 업데이트, {result['skipped']}개 스킵"
            ),
        )


class SaveResultUseCase:
    def __init__(
        self,
        service: LessonService = Depends(),
        progress_repo: UserLessonProgressRepository = Depends(
            get_user_lesson_progress_repository
        ),
    ):
        self.service = service
        self.progress_repo = progress_repo

    def execute(self, req: SaveResultRequestDto, user_id: int) -> SaveResultResponseDto:
        # lesson 존재 여부 확인 (없으면 404)
        self.service.get_lesson(req.lesson_id)
        is_passed = req.score >= PASS_THRESHOLD
        new_status = "passed" if is_passed else "failed"

        existing = self.progress_repo.find_by_user_and_lesson(user_id, req.lesson_id)
        if existing is None:
            progress = UserLessonProgress(
                user_id=user_id,
                lesson_id=req.lesson_id,
                status=new_status,
                attempt=req.attempt,
                updated_at=datetime.now(),
            )
            self.progress_repo.save(progress)
        else:
            existing.attempt = req.attempt
            # 이미 passed 라면 유지, 아니면 최신 결과로 갱신
            if existing.status != "passed":
                existing.status = new_status
            existing.updated_at = datetime.now()
            self.progress_repo.save(existing)

        return SaveResultResponseDto(
            lesson_id=req.lesson_id,
            score=req.score,
            is_passed=is_passed,
            attempt=req.attempt,
            pass_threshold=PASS_THRESHOLD,
        )
