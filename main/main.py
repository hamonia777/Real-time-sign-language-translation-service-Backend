from contextlib import asynccontextmanager
import os
from pathlib import Path  # [추가] 정적 파일 경로 처리를 위해 추가
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # [추가] CSS/JS/이미지 등 정적 파일 서빙을 위해 추가
from fastapi.responses import FileResponse  # [추가] HTML 파일을 응답으로 반환하기 위해 추가
from sqlmodel import SQLModel

from main.api.router import api_router
from main.core.config import settings
from main.core.database import engine
from main.core.scheduler import start_scheduler, scheduler

from main.domain.user.entity.user import User  # noqa: F401
from main.domain.learning.entity.lesson import Lesson  # noqa: F401
# 가령: 26/04/19 수정내용: SQLModel.metadata.create_all 이 모든 테이블을 정상적으로 생성할 수 있도록 모델 import 병합
from main.domain.Inquiry.entity.inquiry import Inquiry  # noqa: F401
from main.domain.LearningBasket.entity.learning_basket import LearningBasket  # noqa: F401
from main.domain.LessonWordMapping.entity.lesson_word_mapping import LessonWordMapping  # noqa: F401
from main.domain.StudyLog.entity.study_log import StudyLog  # noqa: F401
from main.domain.UserLessonProgress.entity.user_lesson_progress import UserLessonProgress  # noqa: F401
from main.domain.UserSurveyProfiles.entity.user_survey_profiles import UserSurveyProfile  # noqa: F401
from main.domain.ProfilePhoto.entity.profile_photo import ProfilePhoto  # noqa: F401
from main.domain.Search.entity.search_history import SearchHistory  # noqa: F401

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    print("테이블 생성 완료")
    start_scheduler()
    yield
    scheduler.shutdown()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan, debug=True)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# [추가] frontend/ 폴더의 HTML, CSS, JS, 이미지 등 정적 파일을 FastAPI에서 서빙하기 위해 추가
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/css", StaticFiles(directory=frontend_dir / "css"), name="css")
app.mount("/js", StaticFiles(directory=frontend_dir / "js"), name="js")
app.mount("/images", StaticFiles(directory=frontend_dir / "images"), name="images")
# 가령: 5월 11일 : 수정 내용 - 영상 매핑 JSON을 프론트에서 읽을 수 있도록 data 폴더 서빙
app.mount("/data", StaticFiles(directory=frontend_dir / "data"), name="data")

# 가령: 5월 11일 : 수정 내용 - 수어 학습 1단계 영상 파일 서빙
# 배포 시에는 SIGN_VIDEO_DIR 또는 프론트의 VIDEO_BASE_URL을 S3/CloudFront 경로로 교체하면 된다.
default_video_dir = Path.home() / "Downloads" / "data" / "data_set"
video_dir = Path(os.getenv("SIGN_VIDEO_DIR", default_video_dir)).expanduser()
if not video_dir.exists():
    video_dir = frontend_dir / "videos"
app.mount("/videos", StaticFiles(directory=video_dir), name="videos")

# 가령: 26/04/19 수정내용: frontend/logo.png 를 루트 경로로 서빙 (HTML 에서 ../logo.png 참조 대응)
@app.get("/logo.png")
def serve_logo():
    return FileResponse(frontend_dir / "logo.png")

@app.get("/")
def read_root():
    return FileResponse(frontend_dir / "html" / "home.html")

# [추가] /login.html, /register.html 등 페이지별 HTML 파일을 동적으로 서빙
@app.get("/{page}.html")
def serve_page(page: str):
    file_path = frontend_dir / "html" / f"{page}.html"
    if file_path.exists():
        return FileResponse(file_path)
    return {"error": "Page not found"}
