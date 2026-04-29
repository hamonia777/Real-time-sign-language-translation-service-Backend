from sqlmodel import Session, select
from fastapi import Depends

from main.domain.Inquiry.entity.inquiry import Inquiry
from main.core.database import get_db


class InquiryRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, inquiry: Inquiry) -> Inquiry:
        self.db.add(inquiry)
        self.db.commit()
        self.db.refresh(inquiry)
        return inquiry

    def find_by_user_id(self, user_id: int) -> list[Inquiry]:
        return list(self.db.execute(select(Inquiry).where(Inquiry.user_id == user_id).order_by(Inquiry.created_at.desc())).scalars().all())

    def list_all(self) -> list[Inquiry]:
        return list(self.db.execute(select(Inquiry).order_by(Inquiry.created_at.desc())).scalars().all())


def get_inquiry_repository(db: Session = Depends(get_db)) -> InquiryRepository:
    return InquiryRepository(db)
