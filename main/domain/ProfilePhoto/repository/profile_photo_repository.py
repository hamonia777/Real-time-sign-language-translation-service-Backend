from sqlmodel import Session, select
from fastapi import Depends

from main.domain.ProfilePhoto.entity.profile_photo import ProfilePhoto
from main.core.database import get_db


class ProfilePhotoRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, photo_id: int) -> ProfilePhoto | None:
        return self.db.execute(select(ProfilePhoto).where(ProfilePhoto.id == photo_id)).scalars().first()

    def list_all(self) -> list[ProfilePhoto]:
        return list(self.db.execute(select(ProfilePhoto)).scalars().all())

    def count(self) -> int:
        return len(self.list_all())

    def save_all(self, photos: list[ProfilePhoto]) -> None:
        for photo in photos:
            self.db.add(photo)
        self.db.commit()


def get_profile_photo_repository(db: Session = Depends(get_db)) -> ProfilePhotoRepository:
    return ProfilePhotoRepository(db)
