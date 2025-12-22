from sqlalchemy import String, ForeignKey, Integer, Text, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from .base import BaseModel
from .auth import Family
import uuid6
from app.extensions import db

class PetProfile(BaseModel):
    __tablename__ = 'pet_profiles'
    
    family_id: Mapped[uuid6.UUID] = mapped_column(ForeignKey('families.id'), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    breed: Mapped[Optional[str]] = mapped_column(String(255))
    birth_date: Mapped[Optional[str]] = mapped_column(String(50)) # ISO Date string or Date object. Keeping string for simplicity or Date? Date is better.
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1024))
    
    family: Mapped["Family"] = relationship(back_populates="pets")

# Association Table for Media <-> Tag
media_tags = Table(
    'media_tags',
    db.metadata,
    Column('media_id', db.Uuid, ForeignKey('media.id'), primary_key=True),
    Column('tag_id', db.Uuid, ForeignKey('tags.id'), primary_key=True)
)

class Tag(BaseModel):
    __tablename__ = 'tags'
    
    family_id: Mapped[uuid6.UUID] = mapped_column(ForeignKey('families.id'), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # media relationship via secondary

class Media(BaseModel):
    __tablename__ = 'media'
    
    family_id: Mapped[uuid6.UUID] = mapped_column(ForeignKey('families.id'), nullable=False, index=True)
    uploader_id: Mapped[uuid6.UUID] = mapped_column(ForeignKey('users.id'), nullable=False)
    
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    duration_sec: Mapped[Optional[float]] = mapped_column(Integer) # Float? Integer in design?
    
    taken_at: Mapped[Optional[str]] = mapped_column(String(50)) # ISO string
    
    status: Mapped[str] = mapped_column(String(50), default='processing', index=True) # processing, ready, error
    
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(1024))
    
    family: Mapped["Family"] = relationship(back_populates="media")
    tags: Mapped[List["Tag"]] = relationship(secondary=media_tags, backref="media")
    
    # Albums association can also be here or in Album

class Album(BaseModel):
    __tablename__ = 'albums'
    
    family_id: Mapped[uuid6.UUID] = mapped_column(ForeignKey('families.id'), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    family: Mapped["Family"] = relationship(back_populates="albums")
    
    # Many-to-Many with Media (Simplified for now, can use association object if ordering is needed)
    media: Mapped[List["Media"]] = relationship(secondary="album_media")

album_media = Table(
    'album_media',
    db.metadata,
    Column('album_id', db.Uuid, ForeignKey('albums.id'), primary_key=True),
    Column('media_id', db.Uuid, ForeignKey('media.id'), primary_key=True),
    Column('created_at', db.DateTime, default=db.func.now())
)
