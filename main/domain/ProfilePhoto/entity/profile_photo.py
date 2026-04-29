from typing import Optional
from sqlmodel import SQLModel, Field


class ProfilePhoto(SQLModel, table=True):
    __tablename__ = "profile_photos"

    id: Optional[int] = Field(default=None, primary_key=True)
    photo_url: str = Field(max_length=500)
    name: str = Field(max_length=50)
