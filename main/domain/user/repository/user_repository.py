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
        return self.db.exec(statement).first()

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return SqlUserRepository(db)