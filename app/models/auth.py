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
    
    # Relationships
    family_memberships: Mapped[List["FamilyMember"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Family(BaseModel):
    __tablename__ = 'families'

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Relationships
    members: Mapped[List["FamilyMember"]] = relationship(back_populates="family", cascade="all, delete-orphan")
    pets: Mapped[List["PetProfile"]] = relationship(back_populates="family", cascade="all, delete-orphan")
    media: Mapped[List["Media"]] = relationship(back_populates="family")
    albums: Mapped[List["Album"]] = relationship(back_populates="family")

class FamilyMember(BaseModel):
    __tablename__ = 'family_members'
    
    family_id: Mapped[uuid6.UUID] = mapped_column(ForeignKey('families.id'), nullable=False)
    user_id: Mapped[uuid6.UUID] = mapped_column(ForeignKey('users.id'), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default='member')  # admin, member
    
    family: Mapped["Family"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="family_memberships")
