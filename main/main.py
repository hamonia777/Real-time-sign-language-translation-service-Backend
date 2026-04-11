from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from main.api.router import api_router
from main.core.config import settings
from main.core.database import engine

from main.domain.user.entity.user import User
from main.domain.UserLessonProgress.entity.user_lesson_progress import UserLessonProgress
from main.domain.UserSurveyProfiles.entity.user_survey_profiles import UserSurveyProfile
from main.domain.Lesson.entity.lesson import Lesson
from main.domain.LearningBasket.entity.learning_basket import LearningBasket
from main.domain.Inquiry.entity.inquiry import Inquiry
from main.domain.LessonWordMapping.entity.lesson_word_mapping import LessonWordMapping
from main.domain.StudyLog.entity.study_log import StudyLog  

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

@app.get("/")
def read_root():
    return {"Hello": "World"}