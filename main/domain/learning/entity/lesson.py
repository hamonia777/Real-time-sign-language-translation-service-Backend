from typing import Optional
from sqlmodel import Field, SQLModel


class Lesson(SQLModel, table=True):
    __tablename__ = "lessons"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255, nullable=False)
    category: str = Field(max_length=20, nullable=False)
    subcategory: Optional[str] = Field(default=None, max_length=50)
    level: int = Field(default=1, nullable=False)
    video_url: str = Field(default="", max_length=500, nullable=False)
    thumbnail_url: Optional[str] = Field(default=None, max_length=500)
    search_count: int = Field(default=0, nullable=False)
