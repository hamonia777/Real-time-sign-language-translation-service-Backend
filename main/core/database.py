from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from main.core.config import settings

# 26.05.08 : 가령 : 수정 내용 - MySQL 유휴 연결 끊김으로 인한 2013 오류 방지를 위해 pool_pre_ping/recycle 적용
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
