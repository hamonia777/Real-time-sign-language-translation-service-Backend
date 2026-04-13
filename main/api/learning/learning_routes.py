import base64
import json

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from main.domain.learning.dto.lesson_dto import (
    LessonListResponseDto,
    LessonResponseDto,
    SaveResultRequestDto,
    SaveResultResponseDto,
    SeedResponseDto,
)
from main.domain.learning.usecase.lesson_usecase import (
    GetLessonUseCase,
    ListLessonsUseCase,
    SaveResultUseCase,
    SeedFingerspellUseCase,
)

router = APIRouter()


@router.post("/seed/fingerspell", response_model=SeedResponseDto)
def seed_fingerspell(usecase: SeedFingerspellUseCase = Depends()):
    return usecase.execute()


@router.get("/lessons", response_model=LessonListResponseDto)
def list_lessons(
    category: str = Query("fingerspell"),
    usecase: ListLessonsUseCase = Depends(),
):
    return usecase.execute(category)


@router.get("/lessons/{lesson_id}", response_model=LessonResponseDto)
def get_lesson(lesson_id: int, usecase: GetLessonUseCase = Depends()):
    return usecase.execute(lesson_id)


@router.post("/results", response_model=SaveResultResponseDto)
def save_result(
    body: SaveResultRequestDto,
    usecase: SaveResultUseCase = Depends(),
):
    return usecase.execute(body)


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
