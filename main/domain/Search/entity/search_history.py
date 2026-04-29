from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field,Relationship

class SearchHistory(SQLModel, table=True):
    __tablename__ = "search_histories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    word: str = Field(max_length=255)
    searched_at: datetime = Field(default_factory=datetime.now)

    user: "User" = Relationship(back_populates="search_histories")