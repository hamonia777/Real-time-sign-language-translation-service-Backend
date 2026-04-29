# 가령: 26/04/19 수정내용: SaveResultUseCase 가 user_id 를 받아 user_lesson_progress 에 upsert 하도록 변경
from datetime import datetime

from fastapi import Depends

from main.domain.UserLessonProgress.entity.user_lesson_progress import UserLessonProgress
from main.domain.UserLessonProgress.repository.user_lesson_progress_repository import (
    UserLessonProgressRepository,
    get_user_lesson_progress_repository,
)
from main.domain.learning.dto.lesson_dto import (
    LessonProgressItemDto,
    LessonListResponseDto,
    LessonResponseDto,
    MyLearningProgressResponseDto,
    SaveResultRequestDto,
    SaveResultResponseDto,
    SeedResponseDto,
    # 가령: 260422: 수정 내용 - 문장 시드 응답 DTO import
    SeedSentencesResponseDto,
    # 가령: 260422: 수정 내용 - 문장+수어어순단어 조회 응답 DTO import
    SentenceWithWordsResponseDto,
    SentenceWordItemDto,
)
from main.domain.learning.service.lesson_service import LessonService


PASS_THRESHOLD = 80.0
MAX_ATTEMPTS = 3


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


# 가령: 260422: 수정 내용 - 문장+수어어순단어 조회 usecase. 문장 학습 페이지 진입 시 호출
class GetSentenceWithWordsUseCase:
    def __init__(self, service: LessonService = Depends()):
        self.service = service

    def execute(self, sentence_id: int) -> SentenceWithWordsResponseDto:
        result = self.service.get_sentence_with_words(sentence_id)
        return SentenceWithWordsResponseDto(
            sentence_id=result["sentence_id"],
            sentence_title=result["sentence_title"],
            words=[SentenceWordItemDto(**w) for w in result["words"]],
        )


# 가령: 260422: 수정 내용 - 문장 시드 usecase. sentences.txt → lessons(category=sentence) + lesson_word_mappings 일괄 적재
class SeedSentencesUseCase:
    def __init__(self, service: LessonService = Depends()):
        self.service = service

    def execute(self) -> SeedSentencesResponseDto:
        result = self.service.seed_sentences()
        missing = result["missing_words"]
        msg = (
            f"문장 시드 완료: {result['inserted_sentences']}개 신규, "
            f"{result['skipped_sentences']}개 재시드(매핑 재생성), "
            f"매핑 {result['inserted_mappings']}개 insert / {result['deleted_mappings']}개 delete"
        )
        if missing:
            msg += f" — 매칭 실패 단어 {len(missing)}개: {missing[:5]}{'...' if len(missing) > 5 else ''}"
        return SeedSentencesResponseDto(
            inserted_sentences=result["inserted_sentences"],
            skipped_sentences=result["skipped_sentences"],
            inserted_mappings=result["inserted_mappings"],
            deleted_mappings=result["deleted_mappings"],
            missing_words=missing,
            total_lines=result["total_lines"],
            message=msg,
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


class GetMyLearningProgressUseCase:
    def __init__(
        self,
        progress_repo: UserLessonProgressRepository = Depends(
            get_user_lesson_progress_repository
        ),
    ):
        self.progress_repo = progress_repo

    def execute(self, user_id: int) -> MyLearningProgressResponseDto:
        completed: list[LessonProgressItemDto] = []
        in_progress: list[LessonProgressItemDto] = []

        for progress, lesson in self.progress_repo.find_by_user_with_lessons(user_id):
            is_completed = progress.status == "passed" or progress.attempt >= MAX_ATTEMPTS
            progress_percent = 100 if is_completed else self._in_progress_percent(progress.attempt)
            item = LessonProgressItemDto(
                lesson_id=lesson.id,
                title=lesson.title,
                category=lesson.category,
                subcategory=lesson.subcategory,
                level=lesson.level,
                status=progress.status or "in_progress",
                attempt=progress.attempt,
                progress_percent=progress_percent,
                updated_at=progress.updated_at,
            )

            if is_completed:
                completed.append(item)
            else:
                in_progress.append(item)

        return MyLearningProgressResponseDto(
            completed_count=len(completed),
            in_progress_count=len(in_progress),
            completed=completed,
            in_progress=in_progress,
        )

    @staticmethod
    def _in_progress_percent(attempt: int) -> int:
        if attempt <= 0:
            return 0
        return min(90, max(10, round((attempt / MAX_ATTEMPTS) * 100)))
