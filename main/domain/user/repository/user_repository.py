from abc import ABC, abstractmethod
from sqlmodel import Session, select
from fastapi import Depends

from main.domain.user.entity.user import User
from main.core.database import get_db
class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    def find_by_kakao_id(self, kakao_id: str) -> User | None:
        pass

    @abstractmethod
    async def find_by_id(self, user_id: int) -> User | None:
        pass
        
    @abstractmethod
    async def save_survey(self, survey) -> None:
        pass

class SqlUserRepository(UserRepository):
    def __init__(self, db: Session):
        self.db = db

    async def save(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def find_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        result = self.db.execute(statement)
        return result.scalars().first()

    def find_by_kakao_id(self, kakao_id: str) -> User | None:
        statement = select(User).where(User.kakao_id == kakao_id)
        result = self.db.execute(statement)
        return result.scalars().first()

    async def find_by_id(self, user_id: int) -> User | None:
        statement = select(User).where(User.id == user_id)
        result = self.db.execute(statement)
        return result.scalars().first()

    async def save_survey(self, survey) -> None:
        self.db.add(survey)
        self.db.commit()

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return SqlUserRepository(db)