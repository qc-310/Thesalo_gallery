from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin
from typing import List, Optional
from .base import BaseModel
import uuid6

class User(BaseModel, UserMixin):
    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    google_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1024))
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    bio: Mapped[Optional[str]] = mapped_column(String(1024))
    
    # Relationships
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    bio: Mapped[Optional[str]] = mapped_column(String(1024))

