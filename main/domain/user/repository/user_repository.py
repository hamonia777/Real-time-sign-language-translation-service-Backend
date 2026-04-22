# 가령: 26/04/19 수정내용: Kakao 로그인 지원(learning) + Survey 저장 기능(master) 병합 및 async 오용 버그 수정
from abc import ABC, abstractmethod
from sqlmodel import Session, select
from fastapi import Depends

from main.domain.user.entity.user import User
from main.core.database import get_db


class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> User:
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    def find_by_kakao_id(self, kakao_id: str) -> User | None:
        pass

    @abstractmethod
    def find_by_id(self, user_id: int) -> User | None:
        pass
        
    @abstractmethod
    def save_survey(self, survey) -> None:
        pass


class SqlUserRepository(UserRepository):
    def __init__(self, db: Session):
        self.db = db

    def save(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def find_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.db.execute(statement).scalars().first()

    def find_by_kakao_id(self, kakao_id: str) -> User | None:
        statement = select(User).where(User.kakao_id == kakao_id)
        return self.db.execute(statement).scalars().first()

    def find_by_id(self, user_id: int) -> User | None:
        statement = select(User).where(User.id == user_id)
        return self.db.execute(statement).scalars().first()

    def save_survey(self, survey) -> None:
        self.db.add(survey)
        self.db.commit()


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return SqlUserRepository(db)