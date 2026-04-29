import base64
import json

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from main.core.security import get_current_user_id
from main.domain.learning.dto.lesson_dto import (
    LessonListResponseDto,
    LessonResponseDto,
    MyLearningProgressResponseDto,
    SaveResultRequestDto,
    SaveResultResponseDto,
    SeedResponseDto,
    # 가령: 260422: 수정 내용 - 문장 시드 응답 DTO import
    SeedSentencesResponseDto,
    # 가령: 260422: 수정 내용 - 문장+수어어순단어 응답 DTO import
    SentenceWithWordsResponseDto,
)
from main.domain.learning.usecase.lesson_usecase import (
    GetLessonUseCase,
    GetMyLearningProgressUseCase,
    ListLessonsUseCase,
    SaveResultUseCase,
    SeedFingerspellUseCase,
    SeedWordsUseCase,
    # 가령: 260422: 수정 내용 - 문장 시드 usecase import
    SeedSentencesUseCase,
    # 가령: 260422: 수정 내용 - 문장+단어 조회 usecase import
    GetSentenceWithWordsUseCase,
)

router = APIRouter()


@router.post("/seed/fingerspell", response_model=SeedResponseDto)
def seed_fingerspell(usecase: SeedFingerspellUseCase = Depends()):
    return usecase.execute()


# 가령: 26/04/19 수정내용: 단어 시드 엔드포인트 신규 추가
@router.post("/seed/word", response_model=SeedResponseDto)
def seed_word(usecase: SeedWordsUseCase = Depends()):
    return usecase.execute()


# 가령: 260422: 수정 내용 - 문장 시드 엔드포인트 신규 추가 (sentences.txt → lessons + lesson_word_mappings)
@router.post("/seed/sentences", response_model=SeedSentencesResponseDto)
def seed_sentences(usecase: SeedSentencesUseCase = Depends()):
    return usecase.execute()


# 가령: 260422: 수정 내용 - 문장 학습 페이지 진입 시 호출. 문장 + 수어 어순 단어 목록 한 번에 반환
@router.get("/sentences/{sentence_id}/words", response_model=SentenceWithWordsResponseDto)
def get_sentence_words(
    sentence_id: int,
    usecase: GetSentenceWithWordsUseCase = Depends(),
):
    return usecase.execute(sentence_id)


@router.get("/lessons", response_model=LessonListResponseDto)
def list_lessons(
    category: str = Query("fingerspell"),
    usecase: ListLessonsUseCase = Depends(),
):
    return usecase.execute(category)


@router.get("/lessons/{lesson_id}", response_model=LessonResponseDto)
def get_lesson(lesson_id: int, usecase: GetLessonUseCase = Depends()):
    return usecase.execute(lesson_id)


@router.get("/my-progress", response_model=MyLearningProgressResponseDto)
def get_my_learning_progress(
    usecase: GetMyLearningProgressUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    return usecase.execute(user_id)


# 가령: 26/04/19 수정내용: /results 엔드포인트에 JWT 인증 필수로 변경 + user_id 를 usecase 에 전달
@router.post("/results", response_model=SaveResultResponseDto)
def save_result(
    body: SaveResultRequestDto,
    usecase: SaveResultUseCase = Depends(),
    user_id: int = Depends(get_current_user_id),
):
    return usecase.execute(body, user_id)


@router.websocket("/ws/recognition")
async def recognition_ws(ws: WebSocket):
    """
    프론트가 {"type":"frame","image":"data:image/jpeg;base64,...","target":"ㄱ"}
    보내면 Top-3 예측을 돌려준다.
    """
    await ws.accept()

    try:
        import cv2
        import numpy as np
        from main.domain.learning.service.recognition_service import RecognitionService

        service = RecognitionService.instance()
    except Exception as e:
        await ws.send_json({"type": "error", "message": f"model load failed: {e}"})
        await ws.close()
        return

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "error", "message": "invalid json"})
                continue

            if msg.get("type") != "frame":
                continue

            image_b64 = msg.get("image", "")
            target = msg.get("target")

            if "," in image_b64:
                image_b64 = image_b64.split(",", 1)[1]

            try:
                img_bytes = base64.b64decode(image_b64)
                arr = np.frombuffer(img_bytes, dtype=np.uint8)
                frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if frame is None:
                    raise ValueError("decode returned None")
            except Exception as e:
                await ws.send_json({"type": "error", "message": f"decode: {e}"})
                continue

            result = service.predict_from_frame(frame)

            top3 = result["top3"]
            score = 0.0
            is_passed = False
            if target and top3:
                for item in top3:
                    if item["label"] == target:
                        score = item["prob"]
                        break
                if top3[0]["label"] == target and top3[0]["prob"] >= 80.0:
                    is_passed = True

            await ws.send_json(
                {
                    "type": "prediction",
                    "hand_detected": result["hand_detected"],
                    "top3": top3,
                    "target": target,
                    "score": score,
                    "is_passed": is_passed,
                }
            )
    except WebSocketDisconnect:
        return
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
            await ws.close()
        except Exception:
            pass


# 가령: 26/04/19 수정내용: 단어 실시간 인식 WebSocket 신규 추가 (model_word.pt 연결)
@router.websocket("/ws/word_recognition")
async def word_recognition_ws(ws: WebSocket):
    """
    client → {"type":"frame","image":"data:image/jpeg;base64,...","target":"안녕하세요"}
    server → {"type":"prediction", "motion": "...", "hand_detected": bool, "live_label": ..., "live_conf": ...,
              "segment_top3": [...], "score": ..., "is_passed": bool, "target": "안녕하세요"}
    """
    await ws.accept()

    try:
        import cv2
        import numpy as np
        from main.domain.learning.service.word_recognition_service import (
            WordRecognitionService,
            WordSession,
        )
        service = WordRecognitionService.instance()
    except Exception as e:
        await ws.send_json({"type": "error", "message": f"model load failed: {e}"})
        await ws.close()
        return

    session = WordSession(service)

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "error", "message": "invalid json"})
                continue

            if msg.get("type") != "frame":
                continue

            image_b64 = msg.get("image", "")
            target = msg.get("target")
            # 가령: 26/04/19 수정내용: 카테고리 필터링용 category/subcategory 전달
            category = msg.get("category")
            subcategory = msg.get("subcategory")
            if "," in image_b64:
                image_b64 = image_b64.split(",", 1)[1]

            try:
                img_bytes = base64.b64decode(image_b64)
                arr = np.frombuffer(img_bytes, dtype=np.uint8)
                frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if frame is None:
                    raise ValueError("decode returned None")
            except Exception as e:
                await ws.send_json({"type": "error", "message": f"decode: {e}"})
                continue

            result = session.process_frame(frame, target, category, subcategory)
            await ws.send_json({"type": "prediction", **result})
    except WebSocketDisconnect:
        return
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
            await ws.close()
        except Exception:
            pass
