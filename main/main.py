from contextlib import asynccontextmanager
from pathlib import Path  # [추가] 정적 파일 경로 처리를 위해 추가
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # [추가] CSS/JS/이미지 등 정적 파일 서빙을 위해 추가
from fastapi.responses import FileResponse  # [추가] HTML 파일을 응답으로 반환하기 위해 추가
from sqlmodel import SQLModel

from main.api.router import api_router
from main.core.config import settings
from main.core.database import engine

from main.domain.user.entity.user import User
from main.domain.learning.entity.lesson import Lesson  # noqa: F401
from main.domain.Inquiry.entity.inquiry import Inquiry
from main.domain.LearningBasket.entity.learning_basket import LearningBasket
from main.domain.LessonWordMapping.entity.lesson_word_mapping import LessonWordMapping
from main.domain.StudyLog.entity.study_log import StudyLog
from main.domain.UserLessonProgress.entity.user_lesson_progress import UserLessonProgress
from main.domain.UserSurveyProfiles.entity.user_survey_profiles import UserSurveyProfile

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    print("테이블 생성 완료")
    yield

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

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

# [수정] 기존 JSON 응답 대신 home.html을 메인 페이지로 반환하도록 변경
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

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