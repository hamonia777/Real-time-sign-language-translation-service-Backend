from typing import Optional, List
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, TEXT

class Inquiry(SQLModel, table=True):
    __tablename__ = "inquiries"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    title: Optional[str] = Field(default=None, max_length=255)
    content: Optional[str] = Field(default=None, sa_column=Column(TEXT))
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    user: "User" = Relationship(back_populates="inquiries")